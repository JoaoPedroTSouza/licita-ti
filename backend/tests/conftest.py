import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_DB = Path(__file__).parent / "test.db"
if _DB.exists():
    _DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_DB}"
os.environ["APP_PASSWORD"] = "segredo"
os.environ["JWT_SECRET"] = "jwt-teste"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["VAPID_PUBLIC_KEY"] = ""
os.environ["VAPID_PRIVATE_KEY"] = ""
