from __future__ import annotations

from typing import Any

from jinja2 import Environment, StrictUndefined


_ENV = Environment(
    undefined=StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render(template_text: str, **context: Any) -> str:
    template = _ENV.from_string(template_text)
    return template.render(**context)


def extract_requirements_excerpt(prompt: str, *, marker: str = "## Novel Content") -> str:
    text = prompt or ""
    idx = text.find(marker)
    if idx < 0:
        return text.strip()
    return text[:idx].strip()


def truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
