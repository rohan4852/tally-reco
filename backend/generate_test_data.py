"""
generate_test_data.py
---------------------
Run this script from the backend/ directory to generate two test Excel files:
  - test_gst_export.xlsx   (simulates a GSTR2B portal export)
  - test_tally_export.xlsx (simulates a Tally Excel export)

Usage:
    python generate_test_data.py

Files are created in backend/uploads/ so you can test parse immediately.
"""

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "uploads"
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Sample data — 10 invoices, mix of matches and intentional mismatches
# ---------------------------------------------------------------------------

GST_DATA = {
    "GSTIN of Supplier":  [
        "27AABCU9603R1ZX", "29AAKFM1997D1ZT", "33AACCV5158R1ZX",
        "24AABCP3518Q1ZF", "07AABCN0091K1ZF", "19AABCP3518Q1ZF",
        "36AABCV9603R1ZX", "27AABCU9603R1ZX", "29AAKFM1997D1ZT",
        "33AACCV5158R1ZX",
    ],
    "Supplier Name": [
        "ABC TRADERS", "XYZ ENTERPRISES", "DELTA SUPPLIERS",
        "GAMMA SOLUTIONS", "BETA CORP", "ALPHA TECH",
        "ZETA GOODS", "ABC TRADERS", "XYZ ENTERPRISES",
        "DELTA SUPPLIERS",
    ],
    "Invoice Number": [
        "INV-001", "INV-002", "INV-003", "INV-004", "INV-005",
        "INV-006", "INV-007", "INV-008", "INV-009", "INV-010",
    ],
    "Invoice Date": [
        "01/04/2024", "05/04/2024", "10/04/2024", "12/04/2024", "15/04/2024",
        "18/04/2024", "20/04/2024", "22/04/2024", "25/04/2024", "28/04/2024",
    ],
    "Taxable Amount": [
        10000.00, 25000.00, 15000.00, 8000.00, 50000.00,
        12000.00, 30000.00, 45000.00, 20000.00, 18000.00,
    ],
    "CGST": [
        900.00, 2250.00, 1350.00, 720.00, 4500.00,
        1080.00, 2700.00, 4050.00, 1800.00, 1620.00,
    ],
    "SGST": [
        900.00, 2250.00, 1350.00, 720.00, 4500.00,
        1080.00, 2700.00, 4050.00, 1800.00, 1620.00,
    ],
    "IGST": [
        0.00, 0.00, 0.00, 0.00, 0.00,
        0.00, 0.00, 0.00, 0.00, 0.00,
    ],
    "Total Amount": [
        11800.00, 29500.00, 17700.00, 9440.00, 59000.00,
        14160.00, 35400.00, 53100.00, 23600.00, 21240.00,
    ],
}

# Tally has same invoices but with intentional differences:
# INV-003 → amount mismatch
# INV-005 → CGST/SGST mismatch
# INV-008 → missing (not in Tally)
# INV-011 → extra in Tally (missing in GST)

TALLY_DATA = {
    "Party GSTIN": [
        "27AABCU9603R1ZX", "29AAKFM1997D1ZT", "33AACCV5158R1ZX",
        "24AABCP3518Q1ZF", "07AABCN0091K1ZF", "19AABCP3518Q1ZF",
        "36AABCV9603R1ZX", "29AAKFM1997D1ZT",  # INV-008 skipped
        "33AACCV5158R1ZX", "22AABCX1234R1ZP",   # extra supplier
    ],
    "Party Name": [
        "ABC TRADERS", "XYZ ENTERPRISES", "Delta Suppliers",   # lowercase mismatch — normalizer fixes
        "GAMMA SOLUTIONS", "BETA CORP", "ALPHA TECH",
        "ZETA GOODS", "XYZ ENTERPRISES",
        "DELTA SUPPLIERS", "NEW VENDOR LTD",
    ],
    "Voucher Number": [
        "INV-001", "INV-002", "INV-003", "INV-004", "INV-005",
        "INV-006", "INV-007", "INV-009",
        "INV-010", "INV-011",             # INV-011 only in Tally
    ],
    "Voucher Date": [
        "01-04-2024", "05-04-2024", "10-04-2024", "12-04-2024", "15-04-2024",
        "18-04-2024", "20-04-2024", "25-04-2024",
        "28-04-2024", "30-04-2024",
    ],
    "Taxable Amount": [
        10000.00, 25000.00, 16000.00,  # INV-003: 15000 in GST vs 16000 here
        8000.00, 50000.00,
        12000.00, 30000.00, 20000.00,
        18000.00, 22000.00,
    ],
    "CGST Amount": [
        900.00, 2250.00, 1440.00,   # INV-003: reflects wrong taxable
        720.00, 5000.00,            # INV-005: 4500 in GST vs 5000 here
        1080.00, 2700.00, 1800.00,
        1620.00, 1980.00,
    ],
    "SGST Amount": [
        900.00, 2250.00, 1440.00,
        720.00, 5000.00,
        1080.00, 2700.00, 1800.00,
        1620.00, 1980.00,
    ],
    "IGST Amount": [
        0.00, 0.00, 0.00, 0.00, 0.00,
        0.00, 0.00, 0.00, 0.00, 0.00,
    ],
    "Total Amount": [
        11800.00, 29500.00, 18880.00,
        9440.00, 60000.00,
        14160.00, 35400.00, 23600.00,
        21240.00, 25960.00,
    ],
}


def generate():
    gst_path = OUTPUT_DIR / "test_gst_export.xlsx"
    tally_path = OUTPUT_DIR / "test_tally_export.xlsx"

    pd.DataFrame(GST_DATA).to_excel(gst_path, index=False, sheet_name="B2B")
    pd.DataFrame(TALLY_DATA).to_excel(tally_path, index=False, sheet_name="Purchase Register")

    print(f"✅  GST test file  : {gst_path}")
    print(f"✅  Tally test file: {tally_path}")
    print()
    print("Intentional mismatches baked in:")
    print("  INV-003 → Taxable amount differs (15000 vs 16000)")
    print("  INV-005 → CGST/SGST differ (4500 vs 5000)")
    print("  INV-008 → Present in GST, MISSING in Tally")
    print("  INV-011 → Present in Tally, MISSING in GST")
    print()
    print("Next: upload both files via POST /upload/ and note the session_id.")
    print("Then: POST /parse/{session_id} to see normalized output.")


if __name__ == "__main__":
    generate()
