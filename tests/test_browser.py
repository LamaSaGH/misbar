from playwright.sync_api import Page, expect


def test_browser_opens(page: Page):
    page.goto("https://example.com")
    expect(page).to_have_title("Example Domain")