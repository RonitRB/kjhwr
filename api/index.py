import sys
from pathlib import Path

# Vercel exposes the repository root to the function; make backend/app a
# top-level import package just as the Docker image does with its /app layout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app as app
