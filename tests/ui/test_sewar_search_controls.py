import re

from playwright.sync_api import Page, expect


SEWAR_HOME_URL = "https://siwar.ksaa.gov.sa/home"


def test_sewar_shared_search_control_is_visible(page: Page):
    response = page.goto(
        SEWAR_HOME_URL,
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    assert response is not None
    assert response.ok

    search_input = page.get_by_role(
        "combobox",
        name=re.compile(
            "اكتب الكلمة (كاملة|مفرقة الحروف)"
        ),
    ).first

    search_button = page.get_by_role(
        "button",
        name=re.compile("ب.*ح.*ث"),
    ).first

    expect(search_input).to_be_visible(timeout=15_000)
    expect(search_button).to_be_visible(timeout=15_000)