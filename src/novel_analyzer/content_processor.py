from __future__ import annotations

from .config_loader import LLMConfig
from . import observability
from .prompts import render


_BOUNDARIES = ["\n\n", "\n", "。", "！", "？", ".", "!", "?"]


def _find_last_boundary(text: str, start: int, end: int) -> int | None:
    best: int | None = None
    for b in _BOUNDARIES:
        idx = text.rfind(b, start, end)
        if idx < 0:
            continue
        cut = idx + len(b)
        if best is None or cut > best:
            best = cut
    return best


def _find_first_boundary(text: str, start: int, end: int) -> int | None:
    best: int | None = None
    for b in _BOUNDARIES:
        idx = text.find(b, start, end)
        if idx < 0:
            continue
        cut = idx
        if best is None or cut < best:
            best = cut
    return best


def _cut_head(text: str, desired: int, window: int) -> int:
    if desired <= 0:
        return 0
    if desired >= len(text):
        return len(text)
    start = max(0, desired - window)
    end = min(len(text), desired + 1)
    boundary = _find_last_boundary(text, start, end)
    return boundary if boundary is not None and boundary > 0 else desired


def _cut_tail(text: str, desired_start: int, window: int) -> int:
    if desired_start <= 0:
        return 0
    if desired_start >= len(text):
        return len(text)
    start = max(0, desired_start)
    end = min(len(text), desired_start + window)
    boundary = _find_first_boundary(text, start, end)
    return boundary if boundary is not None else desired_start


def prepare_content(content: str, cfg: LLMConfig, *, section: str) -> str:
    cp = cfg.content_processing
    max_chars = int(cp.max_chars)
    if max_chars <= 0:
        return content
    if len(content) <= max_chars:
        return content

    marker = render(
        cp.truncation_marker_template,
        original_chars=len(content),
        kept_chars=max_chars,
    )
    marker_len = len(marker)
    window = max(0, int(cp.boundary_search_window))
    boundary_aware = bool(cp.boundary_aware)
    strategy = (cp.strategy or "head_middle_tail").strip().lower()

    def cut_head_slice(n: int) -> str:
        end = n
        if boundary_aware:
            end = _cut_head(content, n, window)
        return content[:end]

    def cut_tail_slice(n: int) -> str:
        start = max(0, len(content) - n)
        if boundary_aware:
            start = _cut_tail(content, start, window)
        return content[start:]

    if strategy in {"head", "start"}:
        head_len = max_chars - marker_len
        out = cut_head_slice(max(0, head_len)) + marker
        out = out[:max_chars]
        observability.truncation(section=section, original_chars=len(content), kept_chars=len(out), strategy=strategy)
        return out

    if strategy in {"tail", "end"}:
        tail_len = max_chars - marker_len
        out = marker + cut_tail_slice(max(0, tail_len))
        out = out[-max_chars:]
        observability.truncation(section=section, original_chars=len(content), kept_chars=len(out), strategy=strategy)
        return out

    if strategy in {"head_tail", "start_end"}:
        available = max_chars - marker_len
        head_len = max(0, available // 2)
        tail_len = max(0, available - head_len)
        out = cut_head_slice(head_len) + marker + cut_tail_slice(tail_len)
        out = out[:max_chars]
        observability.truncation(section=section, original_chars=len(content), kept_chars=len(out), strategy=strategy)
        return out

    if strategy in {"head_middle_tail"}:
        available = max_chars - 2 * marker_len
        if available <= 0:
            out = cut_head_slice(max_chars)
            out = out[:max_chars]
            observability.truncation(section=section, original_chars=len(content), kept_chars=len(out), strategy=strategy)
            return out

        head_len = max(0, available // 3)
        mid_len = max(0, available // 3)
        tail_len = max(0, available - head_len - mid_len)

        head = cut_head_slice(head_len)

        mid_start = max(0, (len(content) // 2) - (mid_len // 2))
        mid_end = min(len(content), mid_start + mid_len)
        if boundary_aware:
            mid_start = _cut_tail(content, mid_start, window)
            mid_end = _cut_head(content, mid_end, window)
            if mid_end < mid_start:
                mid_end = mid_start
        middle = content[mid_start:mid_end]

        tail = cut_tail_slice(tail_len)

        out = head + marker + middle + marker + tail
        out = out[:max_chars]
        observability.truncation(section=section, original_chars=len(content), kept_chars=len(out), strategy=strategy)
        return out

    head_len = max_chars - marker_len
    out = cut_head_slice(max(0, head_len)) + marker
    out = out[:max_chars]
    observability.truncation(section=section, original_chars=len(content), kept_chars=len(out), strategy=strategy)
    return out
