from __future__ import annotations

import io
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import openpyxl
import requests


@dataclass(frozen=True)
class CaseResult:
    name: str
    ok: bool
    detail: str


class HardFail(AssertionError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise HardFail(message)


def _read_xlsx_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _find_test_fixture(prefix: str, uploads_dir: Path) -> Path:
    matches = sorted(uploads_dir.glob(f"*{prefix}*.xlsx"))
    _assert(matches, f"Missing fixture matching pattern '*{prefix}*.xlsx' in {uploads_dir}")
    return matches[0]


def _post_files(api_base_url: str, gst_bytes: bytes, gst_name: str, tally_bytes: bytes, tally_name: str) -> str:
    url = f"{api_base_url}/upload/"

    files = {
        "gst_file": (
            gst_name,
            io.BytesIO(gst_bytes),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        "tally_file": (
            tally_name,
            io.BytesIO(tally_bytes),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    }

    resp = requests.post(url, files=files, timeout=120)
    _assert(200 <= resp.status_code < 300, f"Upload failed: {resp.status_code} {resp.text}")
    data = resp.json()
    _assert("session_id" in data, f"Upload response missing session_id: {data}")
    return data["session_id"]


def _post_reconcile(api_base_url: str, session_id: str) -> Dict:
    url = f"{api_base_url}/reconcile/{session_id}"
    resp = requests.post(url, timeout=180)
    _assert(200 <= resp.status_code < 300, f"Reconcile failed: {resp.status_code} {resp.text}")
    data = resp.json()
    _assert("summary" in data, f"Reconcile response missing summary: {data}")
    return data


def _get_report(api_base_url: str, session_id: str) -> Tuple[bytes, Dict[str, str]]:
    url = f"{api_base_url}/reconcile/reports/{session_id}"
    resp = requests.get(url, timeout=180)
    _assert(200 <= resp.status_code < 300, f"Report download failed: {resp.status_code} {resp.text}")
    headers = {k: v for k, v in resp.headers.items()}
    _assert(len(resp.content) > 0, "Report download returned empty body")
    return resp.content, headers


def _load_workbook_from_bytes(xlsx_bytes: bytes) -> openpyxl.Workbook:
    bio = io.BytesIO(xlsx_bytes)
    wb = openpyxl.load_workbook(bio, data_only=True)
    return wb


def _require_sheet(wb: openpyxl.Workbook, sheet_name: str) -> None:
    _assert(sheet_name in wb.sheetnames, f"Missing expected sheet '{sheet_name}'. Found: {wb.sheetnames}")


def _require_header_row(ws: openpyxl.worksheet.worksheet.Worksheet, expected_headers: List[str]) -> None:
    values = [ws.cell(row=1, column=i + 1).value for i in range(len(expected_headers))]
    values_norm = ["" if v is None else str(v).strip() for v in values]
    _assert(values_norm == expected_headers, f"Header mismatch. Expected={expected_headers} Got={values_norm}")


def _sheet_has_any_data_rows(ws: openpyxl.worksheet.worksheet.Worksheet) -> bool:
    # row 1 is header
    for r in range(2, ws.max_row + 1):
        row_vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
        if any(v not in (None, "") for v in row_vals):
            return True
    return False


def _build_expected_headers() -> Dict[str, List[str]]:
    return {
        "Matched": [
            "GSTIN",
            "Supplier Name",
            "Invoice Number",
            "Invoice Date",
            "Taxable Amount",
            "CGST",
            "SGST",
            "IGST",
            "Match Status",
        ],
        "Mismatches": [
            "GSTIN",
            "Supplier Name",
            "Invoice Number",
            "Invoice Date",
            "GST Taxable Amount",
            "Books Taxable Amount",
            "GST Tax Amount",
            "Books Tax Amount",
            "Mismatch Reason",
            "Remarks",
        ],
        "Missing in GST": [
            "GSTIN",
            "Supplier Name",
            "Invoice Number",
            "Invoice Date",
            "Taxable Amount",
            "Remarks",
        ],
        "Missing in Books": [
            "GSTIN",
            "Supplier Name",
            "Invoice Number",
            "Invoice Date",
            "Taxable Amount",
            "Remarks",
        ],
        "Summary": ["Metric", "Value"],
    }


def _save_report_bytes(output_dir: Path, session_id: str, case_name: str, body: bytes) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{case_name}_reconciliation_{session_id}.xlsx"
    out.write_bytes(body)
    return out


def _make_edge_case_missing_columns(source_path: Path, dest_path: Path) -> None:
    # Strategy: remove the header column that corresponds to taxable amount by inserting an empty value.
    # We edit at the Excel level minimally to trigger parser mapping warnings.
    wb = openpyxl.load_workbook(source_path)
    ws = wb.active

    header_row = None
    for r in range(1, min(15, ws.max_row) + 1):
        row_vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
        row_str = ["" if v is None else str(v).strip().lower() for v in row_vals]
        if any("taxable" in s for s in row_str) or any(s == "taxable amount" for s in row_str):
            header_row = r
            break
    _assert(header_row is not None, "Could not locate taxable amount header row for edge-case fixture")

    # Find a taxable amount-like column and blank out all values beneath it
    taxable_col = None
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=header_row, column=c).value
        if v is None:
            continue
        s = str(v).strip().lower()
        if "taxable" in s:
            taxable_col = c
            break
    _assert(taxable_col is not None, "Could not locate taxable amount column for edge-case fixture")

    for rr in range(header_row + 1, ws.max_row + 1):
        ws.cell(row=rr, column=taxable_col).value = None

    wb.save(dest_path)


def _make_edge_case_duplicate_invoice(source_path: Path, dest_path: Path) -> None:
    wb = openpyxl.load_workbook(source_path)
    ws = wb.active

    header_row = None
    invoice_col = None
    for r in range(1, min(15, ws.max_row) + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=r, column=c).value
            if v is None:
                continue
            s = str(v).strip().lower()
            if s in {"invoice number", "invoice no", "inv no", "voucher number", "bill no", "doc no", "document number"} or "invoice" in s:
                header_row = r
                invoice_col = c
                break
        if header_row is not None:
            break

    _assert(header_row is not None and invoice_col is not None, "Could not locate invoice column for duplicate edge-case fixture")

    # Find first non-empty invoice number row and duplicate it to next available row
    first_inv_row = None
    first_inv_value = None
    for rr in range(header_row + 1, ws.max_row + 1):
        v = ws.cell(row=rr, column=invoice_col).value
        if v is not None and str(v).strip() != "":
            first_inv_row = rr
            first_inv_value = v
            break

    _assert(first_inv_row is not None, "Could not find a row with a non-empty invoice number to duplicate")

    target_row = ws.max_row + 1
    ws.insert_rows(target_row)

    # Copy entire row values
    for c in range(1, ws.max_column + 1):
        ws.cell(row=target_row, column=c).value = ws.cell(row=first_inv_row, column=c).value

    # Ensure invoice number is duplicated
    ws.cell(row=target_row, column=invoice_col).value = first_inv_value

    wb.save(dest_path)


def _make_edge_case_tax_mismatch(gst_source: Path, dest_gst: Path) -> None:
    # Strategy: locate CGST column and change one value to a different amount.
    wb = openpyxl.load_workbook(gst_source)
    ws = wb.active

    header_row = None
    cgst_col = None
    for r in range(1, min(20, ws.max_row) + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=r, column=c).value
            if v is None:
                continue
            s = str(v).strip().lower()
            if s in {"cgst", "cgst amount", "cgst amt", "central tax"} or s.startswith("cgst"):
                header_row = r
                cgst_col = c
                break
        if header_row is not None:
            break

    _assert(header_row is not None and cgst_col is not None, "Could not locate CGST column for tax mismatch edge-case")

    # Modify first numeric CGST-like cell below header
    modified = False
    for rr in range(header_row + 1, ws.max_row + 1):
        v = ws.cell(row=rr, column=cgst_col).value
        if v is None or str(v).strip() == "":
            continue
        try:
            # Keep scale in plausible range
            num = float(str(v).replace(",", ""))
            ws.cell(row=rr, column=cgst_col).value = round(num + 1.23, 2)
            modified = True
            break
        except Exception:
            continue

    _assert(modified, "Could not modify any CGST value to create a tax mismatch")
    wb.save(dest_gst)


def _run_case(api_base_url: str, uploads_dir: Path, output_dir: Path, case_name: str, gst_path: Path, tally_path: Path) -> CaseResult:
    try:
        gst_bytes = _read_xlsx_bytes(gst_path)
        tally_bytes = _read_xlsx_bytes(tally_path)

        session_id = _post_files(
            api_base_url=api_base_url,
            gst_bytes=gst_bytes,
            gst_name=gst_path.name,
            tally_bytes=tally_bytes,
            tally_name=tally_path.name,
        )

        reconcile_data = _post_reconcile(api_base_url, session_id)
        summary = reconcile_data["summary"]
        _assert(isinstance(summary, dict), "Reconcile summary is not a dict")

        report_bytes, _headers = _get_report(api_base_url, session_id)

        wb = _load_workbook_from_bytes(report_bytes)
        expected_headers = _build_expected_headers()

        for sheet, headers in expected_headers.items():
            _require_sheet(wb, sheet)
            if sheet == "Summary":
                _require_header_row(wb[sheet], headers)
            else:
                _require_header_row(wb[sheet], headers)
                # Some edge-case fixtures can legitimately produce 0 matched rows.
                # Hard-fail only when sheet other than 'Matched' is structurally empty.
                if sheet != "Matched":
                    _assert(
                        _sheet_has_any_data_rows(wb[sheet]),
                        f"Sheet '{sheet}' has no data rows",
                    )

        _save_report_bytes(output_dir=output_dir, session_id=session_id, case_name=case_name, body=report_bytes)
        return CaseResult(name=case_name, ok=True, detail="OK")
    except HardFail as e:
        return CaseResult(name=case_name, ok=False, detail=str(e))
    except Exception as e:
        return CaseResult(name=case_name, ok=False, detail=f"Unexpected error: {e}")


def main() -> int:
    api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
    repo_root = Path(__file__).resolve().parent.parent
    backend_dir = repo_root / "backend"
    uploads_dir = backend_dir / "uploads"
    output_dir = repo_root / "outputs" / "day7"
    temp_dir = backend_dir / "temp_day7"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Base fixtures: existing test exports
    gst_fixture = uploads_dir / "test_gst_export.xlsx"
    tally_fixture = uploads_dir / "test_tally_export.xlsx"
    _assert(gst_fixture.exists(), f"Missing {gst_fixture}")
    _assert(tally_fixture.exists(), f"Missing {tally_fixture}")


    results: List[CaseResult] = []

    # Case 1: Happy path end-to-end with existing fixtures
    results.append(
        _run_case(
            api_base_url=api_base_url,
            uploads_dir=uploads_dir,
            output_dir=output_dir,
            case_name="happy_path",
            gst_path=gst_fixture,
            tally_path=tally_fixture,
        )
    )

    # Case 2: Missing columns trigger (taxable column blanked)
    gst_missing_cols = temp_dir / "gst_missing_cols.xlsx"
    tally_missing_cols = temp_dir / "tally_missing_cols.xlsx"

    # Apply missing-column style mutation to GST fixture
    _make_edge_case_missing_columns(gst_fixture, gst_missing_cols)
    # Copy tally unchanged (still required by upload API)
    tally_missing_cols.write_bytes(_read_xlsx_bytes(tally_fixture))

    results.append(
        _run_case(
            api_base_url=api_base_url,
            uploads_dir=uploads_dir,
            output_dir=output_dir,
            case_name="missing_columns",
            gst_path=gst_missing_cols,
            tally_path=tally_missing_cols,
        )
    )

    # Case 3: Duplicate invoice detection (duplicate first invoice row)
    gst_duplicate = temp_dir / "gst_duplicate_invoice.xlsx"
    tally_duplicate = temp_dir / "tally_duplicate_invoice.xlsx"

    _make_edge_case_duplicate_invoice(tally_fixture, tally_duplicate)
    gst_duplicate.write_bytes(_read_xlsx_bytes(gst_fixture))

    results.append(
        _run_case(
            api_base_url=api_base_url,
            uploads_dir=uploads_dir,
            output_dir=output_dir,
            case_name="duplicate_invoice",
            gst_path=gst_duplicate,
            tally_path=tally_duplicate,
        )
    )

    # Case 4: Tax mismatch scenario (change CGST in GST)
    gst_tax_mismatch = temp_dir / "gst_tax_mismatch.xlsx"
    tally_tax_mismatch = temp_dir / "tally_tax_mismatch.xlsx"

    _make_edge_case_tax_mismatch(gst_fixture, gst_tax_mismatch)
    tally_tax_mismatch.write_bytes(_read_xlsx_bytes(tally_fixture))

    results.append(
        _run_case(
            api_base_url=api_base_url,
            uploads_dir=uploads_dir,
            output_dir=output_dir,
            case_name="tax_mismatch",
            gst_path=gst_tax_mismatch,
            tally_path=tally_tax_mismatch,
        )
    )

    failed = [r for r in results if not r.ok]
    print("Day 7 E2E Results:")
    for r in results:
        status = "PASS" if r.ok else "FAIL"
        print(f"- {r.name}: {status} ({r.detail})")

    if failed:
        print(f"\nHard failures: {len(failed)}")
        return 1

    return 0


if __name__ == "__main__":
    # Make sure stdout flushes quickly for CI logs
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())