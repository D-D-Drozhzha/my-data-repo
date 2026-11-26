# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Register the Garmin MCP server in Claude Desktop's config (keeps a backup and other servers)."""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

uv, server = sys.argv[1], sys.argv[2]
cfg_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
cfg_path.parent.mkdir(parents=True, exist_ok=True)
cfg = {}
if cfg_path.exists():
    backup = cfg_path.with_suffix(f".backup-{datetime.now():%Y%m%d-%H%M%S}.json")
    shutil.copy2(cfg_path, backup)
    print(f"   резервная копия конфига: {backup}")
    try:
        cfg = json.loads(cfg_path.read_text() or "{}")
    except json.JSONDecodeError:
        sys.exit(f"❌ {cfg_path} — некорректный JSON, поправьте вручную (копия сохранена).")
cfg.setdefault("mcpServers", {})["garmin"] = {"command": uv, "args": ["run", "--script", server]}
cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
print(f"   добавлен сервер 'garmin' в {cfg_path}")
