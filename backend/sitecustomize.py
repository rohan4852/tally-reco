from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Add backend/ to sys.path if missing so `import app` works.
backend_dir = str(HERE)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)