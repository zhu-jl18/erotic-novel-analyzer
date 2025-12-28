from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


_logger = logging.getLogger("novel_analyzer.llm")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _emit(level: int, payload: dict[str, Any]) -> None:
    try:
        payload = dict(payload)
        payload.setdefault("ts", _utc_iso())
        _logger.log(level, json.dumps(payload, ensure_ascii=False))
    except Exception:
        return


def retry(*, section: str, attempt: int, max_attempts: int, reason: str, wait_seconds: float) -> None:
    _emit(
        logging.WARNING,
        {
            "event": "llm_retry",
            "section": section,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "reason": reason,
            "wait_seconds": wait_seconds,
        },
    )


def truncation(*, section: str, original_chars: int, kept_chars: int, strategy: str) -> None:
    ratio = 0.0
    if original_chars > 0:
        ratio = round(kept_chars / original_chars, 4)
    _emit(
        logging.INFO,
        {
            "event": "content_truncation",
            "section": section,
            "original_chars": original_chars,
            "kept_chars": kept_chars,
            "ratio": ratio,
            "strategy": strategy,
        },
    )


def repair(*, section: str, success: bool, reason: str, errors: list[str] | None = None) -> None:
    _emit(
        logging.INFO,
        {
            "event": "llm_repair",
            "section": section,
            "reason": reason,
            "success": success,
            "errors": errors or [],
        },
    )


def function_calling_protocol_fallback(*, section: str, reason: str) -> None:
    _emit(
        logging.WARNING,
        {
            "event": "function_calling_protocol_fallback",
            "section": section,
            "reason": reason,
        },
    )


def missing_tool_call(*, section: str, reason: str) -> None:
    _emit(
        logging.ERROR,
        {
            "event": "function_calling_missing_tool_call",
            "section": section,
            "reason": reason,
        },
    )
