# GST Reconciliation MVP

Automates reconciliation between GST portal exports (GSTR1/GSTR2A/GSTR2B) and Tally Excel exports.

---

## Day 1 — Backend Setup

### Folder structure

```
gst-reconciliation-mvp/
└── backend/
    ├── app/
    │   ├── main.py              # FastAPI app entry point
    │   ├── config.py            # Paths, constants, settings
    │   ├── routes/
    │   │   ├── health.py        # GET /health
    │   │   └── upload.py        # POST /upload, GET /upload/list, DELETE /upload/{session_id}
    │   ├── schemas/
    │   │   └── upload.py        # Pydantic response models
    │   ├── utils/
    │   │   └── file_utils.py    # Validation, naming, streaming save
    │   ├── services/            # (Day 2+) parser, reconciliation, report services
    │   ├── matching/            # (Day 3+) engine, classifier, comparator
    │   └── reports/             # (Day 5+) OpenPyXL report generator
    ├── uploads/                 # Uploaded Excel files land here
    ├── outputs/                 # Generated reports go here
    └── requirements.txt
```

### Setup (run once)

```bash
cd gst-reconciliation-mvp/backend

# Create and activate virtual environment
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the server

```bash
# From backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Verify

| Check | URL |
|---|---|
| Root ping | http://localhost:8000/ |
| Health check | http://localhost:8000/health |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### Test upload via curl

```bash
curl -X POST http://localhost:8000/upload/ \
  -F "gst_file=@/path/to/GSTR2B.xlsx" \
  -F "tally_file=@/path/to/Tally_Export.xlsx"
```

Expected response:

```json
{
  "message": "Both files uploaded successfully. Use the session_id to run reconciliation.",
  "session_id": "a1b2c3d4...",
  "gst_file": {
    "original_filename": "GSTR2B.xlsx",
    "saved_filename": "a1b2c3d4_gst_GSTR2B.xlsx",
    "file_size_bytes": 12345,
    "file_type": "gst"
  },
  "tally_file": {
    "original_filename": "Tally_Export.xlsx",
    "saved_filename": "a1b2c3d4_tally_Tally_Export.xlsx",
    "file_size_bytes": 9876,
    "file_type": "tally"
  }
}
```

---

Days 2–7 build on this foundation. Keep the `session_id` from each upload — it's used in all subsequent API calls.
