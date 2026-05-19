from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import requests


@dataclass(frozen=True)
class UploadResult:
    session_id: str
    summary: Dict[str, Any]


class ApiError(RuntimeError):
    pass


def _raise_for_status(response: requests.Response) -> None:
    if 200 <= response.status_code < 300:
        return
    try:
        payload = response.json()
    except Exception:
        payload = {"detail": response.text}
    raise ApiError(f"API error {response.status_code}: {payload}")


def upload_files(api_base_url: str, gst_file, tally_file) -> str:
    url = f"{api_base_url}/upload/"

    files = {
        "gst_file": (gst_file.name, gst_file.getvalue(), gst_file.type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "tally_file": (tally_file.name, tally_file.getvalue(), tally_file.type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    }

    resp = requests.post(url, files=files, timeout=120)
    _raise_for_status(resp)
    data = resp.json()
    return data["session_id"]


def run_reconciliation(api_base_url: str, session_id: str) -> Dict[str, Any]:
    url = f"{api_base_url}/reconcile/{session_id}"
    resp = requests.post(url, timeout=180)
    _raise_for_status(resp)
    data = resp.json()

    # API returns full ReconcileResponse object; summary lives under data["summary"]
    if "summary" not in data:
        raise ApiError(f"Unexpected reconcile response (missing summary): {data}")
    return data["summary"]


def get_download_url(api_base_url: str, session_id: str) -> str:
    return f"{api_base_url}/reconcile/reports/{session_id}"


def reconcile_upload_and_run(api_base_url: str, gst_file, tally_file) -> Tuple[str, Dict[str, Any]]:
    session_id = upload_files(api_base_url=api_base_url, gst_file=gst_file, tally_file=tally_file)
    summary = run_reconciliation(api_base_url=api_base_url, session_id=session_id)
    return session_id, summary

