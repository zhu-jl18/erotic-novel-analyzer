from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


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
    SectionConfig,
)
from novel_analyzer.llm_client import LLMClient, LLMRuntime
from novel_analyzer.schemas import MetaOutput


class _FakeResponse:
    def __init__(self, status_code: int, *, text: str, json_obj: dict | None = None):
        self.status_code = status_code
        self.text = text
        self._json_obj = json_obj

    def json(self):
        if self._json_obj is None:
            raise ValueError("no json")
        return self._json_obj


def _make_cfg() -> LLMConfig:
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
            max_chars=100,
            strategy="head",
            boundary_aware=False,
            boundary_search_window=200,
            truncation_marker_template="...[TRUNCATED]...",
        ),
        repair=RepairConfig(enabled=True, max_attempts=1, prompt_head_max_chars=5000, bad_output_max_chars=5000),
        sections={
            "meta": SectionConfig(
                temperature=0.0,
                tool_name="extract_meta",
                description="meta",
                prompt_template="x",
            )
        },
        repair_template=RepairTemplateConfig(
            temperature=0.0,
            prompt_template="""
You are a strict tool-call argument fixer.

## Bad output
{{ bad_output }}

## Validation errors
{{ validation_errors }}
""".strip(),
        ),
    )


def test_repair_pass_fixes_schema(monkeypatch):
    runtime = LLMRuntime(api_url="http://example.com/v1", api_key="sk", model="m")
    cfg = _make_cfg()
    client = LLMClient(runtime, cfg)

    prompts: list[str] = []

    bad_args = {
        "novel_info": {
            "world_setting": "现代",
            "world_tags": ["都市"],
            "chapter_count": 1,
            "is_completed": False,
            "completion_note": "",
        },
        "summary": "",  # invalid: empty
    }

    fixed_args = {
        "novel_info": {
            "world_setting": "现代",
            "world_tags": ["都市"],
            "chapter_count": 1,
            "is_completed": False,
            "completion_note": "",
        },
        "summary": "修复后",
    }

    def make_data(args: dict):
        return {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "extract_meta",
                                    "arguments": json.dumps(args, ensure_ascii=False),
                                }
                            }
                        ]
                    }
                }
            ]
        }

    responses = [
        _FakeResponse(200, text=json.dumps(make_data(bad_args), ensure_ascii=False), json_obj=make_data(bad_args)),
        _FakeResponse(200, text=json.dumps(make_data(fixed_args), ensure_ascii=False), json_obj=make_data(fixed_args)),
    ]

    def fake_post(url, headers=None, json=None, timeout=None):
        prompts.append((json.get("messages") or [{}])[0].get("content") or "")
        return responses.pop(0)

    import novel_analyzer.llm_client as llm_client_mod

    monkeypatch.setattr(llm_client_mod.requests, "post", fake_post)

    out = client.call_section(section="meta", prompt="REQ\n\n## Novel Content\nX", output_model=MetaOutput)
    assert out.summary == "修复后"

    assert len(prompts) == 2
    assert "Bad output" in prompts[1]
    assert "Validation errors" in prompts[1]
