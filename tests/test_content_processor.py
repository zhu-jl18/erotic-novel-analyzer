from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from novel_analyzer.config_loader import (
    ContentProcessingConfig,
    DefaultsConfig,
    LLMConfig,
    RepairConfig,
    RepairTemplateConfig,
    RetryPolicy,
)
from novel_analyzer.content_processor import prepare_content


def _make_cfg(*, max_chars: int, strategy: str, boundary_aware: bool = True) -> LLMConfig:
    return LLMConfig(
        defaults=DefaultsConfig(
            timeout_seconds=10,
            retry=RetryPolicy(
                count=1,
                backoff="linear",
                base_wait_seconds=0,
                max_wait_seconds=0,
                retryable_status_codes=(429, 502, 503, 504),
            ),
        ),
        content_processing=ContentProcessingConfig(
            max_chars=max_chars,
            strategy=strategy,
            boundary_aware=boundary_aware,
            boundary_search_window=200,
            truncation_marker_template="\n\n...[内容已截断: 原文 {{ original_chars }} 字，保留 {{ kept_chars }} 字]...\n\n",
        ),
        repair=RepairConfig(enabled=True, max_attempts=1, prompt_head_max_chars=100, bad_output_max_chars=100),
        sections={},
        repair_template=RepairTemplateConfig(temperature=0.1, prompt_template="repair"),
    )


def test_prepare_content_head_middle_tail_includes_marker_and_bounds_length():
    cfg = _make_cfg(max_chars=220, strategy="head_middle_tail", boundary_aware=True)

    content = ("A。\n" * 80) + "\n\n" + ("B。\n" * 80) + "\n\n" + ("C。\n" * 80)

    out = prepare_content(content, cfg, section="meta")

    assert len(out) <= 220
    assert "内容已截断" in out
    assert "原文" in out and "保留" in out
    # head/middle/tail sampling should preserve signal from each region
    assert "A" in out
    assert "B" in out
    assert "C" in out


def test_prepare_content_head_strategy_appends_marker():
    cfg = _make_cfg(max_chars=80, strategy="head", boundary_aware=False)
    content = "x" * 500

    out = prepare_content(content, cfg, section="core")

    assert len(out) <= 80
    assert "内容已截断" in out
