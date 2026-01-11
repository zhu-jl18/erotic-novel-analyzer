from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("about:blank")
        page.add_script_tag(path=str(REPO_ROOT / "static" / "chart-view.js"))
        yield page
        browser.close()


def _build_lewd_elements_html(page, analysis: dict) -> str:
    return page.evaluate("analysis => buildLewdElementsHtml(analysis)", analysis)


def test_build_lewd_elements_html_empty(page):
    html = _build_lewd_elements_html(page, {})
    assert "未检测到相关元素" in html
    assert 'data-lucide="sparkles"' in html


def test_build_lewd_elements_html_with_data(page):
    analysis = {
        "lewd_elements": [
            {
                "type": "恋足",
                "example": "足交描写",
                "involved_characters": ["角色A"],
                "chapter_location": "第1章",
            }
        ],
        "lewd_elements_summary": "包含恋足元素",
    }
    html = _build_lewd_elements_html(page, analysis)
    assert "涩情元素概览" in html
    assert "恋足" in html
    assert "足交描写" in html
    assert "包含恋足元素" in html
