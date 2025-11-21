# backend/drafts.py
from pathlib import Path
from . import db
import datetime
import uuid

DATA_DIR = Path("data")
DRAFT_FILE = DATA_DIR / "drafts.json"

def save_draft(draft: dict, data_dir: str = "data"):
    DATA_DIR = Path(data_dir)
    DRAFT_FILE = DATA_DIR / "drafts.json"
    drafts = db.load_json(DRAFT_FILE, default=[])
    # enrich
    new = {
        "id": str(uuid.uuid4()),
        "subject": draft.get("subject","(no subject)"),
        "body": draft.get("body",""),
        "meta": draft.get("meta", {}),
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    drafts.append(new)
    db.save_json(DRAFT_FILE, drafts)
    return new
