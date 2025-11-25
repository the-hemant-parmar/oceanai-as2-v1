
from . import db, prompts as prompts_module
from pathlib import Path
from . import agent as agent_module

def run_ingestion(data_dir: str, prompts: dict = None):
    DATA_DIR = Path(data_dir)
    inbox_file = DATA_DIR / "mock_inbox.json"
    processed_file = DATA_DIR / "processed.json"
    inbox = db.load_json(inbox_file, default=[])
    processed = db.load_json(processed_file, default={})
    if prompts is None:
        prompts = prompts_module.load_prompts()
    for idx, email in enumerate(inbox):
        key = str(email.get("id", idx))
        if key in processed:
            continue
        try:
            category_resp = agent_module.simple_categorize(email, prompts["categorization"])
            actions_resp = agent_module.simple_extract_actions(email, prompts["action_item"])
            processed[key] = {"category": category_resp, "actions": actions_resp}
        except Exception as e:
            processed[key] = {"error": str(e)}
    db.save_json(processed_file, processed)
    return processed
