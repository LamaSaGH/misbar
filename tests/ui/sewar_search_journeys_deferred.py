import re
import pytest

pytestmark = pytest.mark.skip(
    reason="Deferred until the UI regression phase"
)
from playwright.sync_api import Page, expect


SEWAR_HOME_URL = "https://siwar.ksaa.gov.sa/home"


def test_complete_word_search_returns_expected_word(page: Page):
    page.goto(
        SEWAR_HOME_URL,
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    search_input = page.get_by_role(
        "combobox",
        name="ابحث في المعاجم",
    )

search_input.fill("سلام")
search_input.press("Enter")

page.get_by_role(
    "button",
    name="بــحـــث",
).click()

    page.wait_for_url(
        re.compile(
            r"result-page-public/.+searchType=lemma"
        ),
        timeout=20_000,
    )

    result_word = page.locator(
        "span.lemma",
        has_text="سلام",
    ).first

    expect(result_word).to_be_visible(timeout=15_000)