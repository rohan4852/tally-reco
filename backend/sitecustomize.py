from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Ensure the *parent of* the `app/` package is on sys.path.
# We need: backend_dir = <repo>/backend, so that `import app` resolves to <repo>/backend/app.
backend_dir = str(HERE)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# (Optional but safe) also add repo root for other absolute imports.
repo_root = str(HERE.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
