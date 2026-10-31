"""Saves every NAY to data/nays.jsonl (one JSON object per line)."""

import json
import time
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "nays.jsonl"


def log_nay(**fields):
    LOG_PATH.parent.mkdir(exist_ok=True)
    fields["timestamp"] = time.time()
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(fields, ensure_ascii=False) + "\n")
