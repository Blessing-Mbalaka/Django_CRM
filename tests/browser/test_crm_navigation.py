"""Playwright acceptance journey for the primary launcher and CRM navigation."""
import os

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("CRM_TEST_BASE_URL", "http://127.0.0.1:5693")
PRIMARY_TOOLS = [
    "Invoicing",
    "Inventory",
    "Project Management",
    "Marketing",
    "CRM",
    "Documents",
]


def login(page, username="ndlamini"):
    page.goto(f"{BASE_URL}/accounts/login/", wait_until="networkidle")
    page.locator(f'[data-demo-username="{username}"]').click()
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_url(f"{BASE_URL}/academy/")


def run_academy_order(page):
    page.goto(f"{BASE_URL}/academy/#tools", wait_until="networkidle")
    page.wait_for_selector(".academy-tool-card")
    headings = page.locator(".academy-tool-card h2").all_inner_texts()
    assert headings == PRIMARY_TOOLS, headings


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        login(page)
        run_academy_order(page)
        context.close()
        browser.close()
    print("PASS CRM navigation: ordered Academy applications")


if __name__ == "__main__":
    run()
