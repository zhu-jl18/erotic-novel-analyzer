from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from novel_analyzer import observability


def test_retry_emits_json(caplog):
    caplog.set_level(logging.WARNING, logger="novel_analyzer.llm")

    observability.retry(section="meta", attempt=1, max_attempts=3, reason="timeout", wait_seconds=1.5)

    assert caplog.records
    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "llm_retry"
    assert payload["section"] == "meta"
    assert payload["attempt"] == 1


def test_truncation_emits_ratio(caplog):
    caplog.set_level(logging.INFO, logger="novel_analyzer.llm")

    observability.truncation(section="core", original_chars=1000, kept_chars=100, strategy="head")

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "content_truncation"
    assert payload["ratio"] == 0.1
