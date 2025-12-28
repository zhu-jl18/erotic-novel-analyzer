from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from novel_analyzer.config_loader import load_llm_config


def test_load_llm_config_from_fixed_path():
    cfg = load_llm_config(REPO_ROOT)

    assert cfg.defaults.timeout_seconds > 0
    assert cfg.defaults.retry.count >= 1
    assert cfg.defaults.retry.backoff in {"exponential", "linear"}

    assert set(cfg.sections.keys()) == {"meta", "core", "scenes", "thunder"}

    meta = cfg.sections["meta"]
    assert meta.tool_name
    assert "Novel Content" in meta.prompt_template

    assert cfg.repair_template.temperature >= 0
    assert "tool-call argument fixer" in cfg.repair_template.prompt_template
