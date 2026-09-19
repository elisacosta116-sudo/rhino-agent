"""Hook PostToolUse: grava cada chamada ao MCP do Rhino em logs/rhino_calls.jsonl."""
import json, sys, datetime, pathlib

payload = json.load(sys.stdin)
payload["logged_at"] = datetime.datetime.now().isoformat()
log = pathlib.Path("logs") / "rhino_calls.jsonl"
log.parent.mkdir(exist_ok=True)
with log.open("a", encoding="utf-8") as f:
    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
