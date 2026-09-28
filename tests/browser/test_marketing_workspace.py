"""Playwright acceptance journey for the database-backed Marketing workspace."""
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("CRM_TEST_BASE_URL", "http://127.0.0.1:8023")
PASSWORD = "MarketingBrowser123!"


def login(page, username):
    page.goto(f"{BASE_URL}/accounts/login/", wait_until="networkidle")
    page.locator("#id_username").fill(username)
    page.locator("#id_password").fill(PASSWORD)
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_url(f"{BASE_URL}/academy/")


def submit_dialog(page):
    page.locator('#dialogBody button[type="submit"]').first.click()
    page.wait_for_function("() => !document.querySelector('#marketingDialog').open")


def run():
    stamp = str(int(time.time()))
    upload = Path(__file__).resolve().parents[2] / "static" / "sme" / "assets" / "inventory-banner.png"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page_errors, server_errors = [], []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on("response", lambda response: server_errors.append(f"{response.status} {response.url}") if response.status >= 500 else None)
        login(page, "marketing-browser")
        page.goto(f"{BASE_URL}/growth/", wait_until="networkidle")
        page.wait_for_selector('[data-route="dashboard"].active')
        assert page.locator('#marketingNavigation [data-route]').count() == 9
        expected = {
            "dashboard": "Marketing & Advertising", "campaigns": "Campaigns", "advertising": "Advertising",
            "content": "Posters & Content", "email": "Email Marketing", "calendar": "Marketing Calendar",
            "leads": "Marketing Leads", "analytics": "Analytics", "brand": "Brand Kit",
        }
        for route, title in expected.items():
            page.locator(f'[data-route="{route}"]').click()
            page.wait_for_function("title => document.querySelector('#pageTitle')?.textContent === title", arg=title)
        assert page.locator('#providerStatus').inner_text().lower().count('not configured') >= 1

        page.locator('[data-route="campaigns"]').click()
        page.locator('#primaryAction').click()
        campaign_name = f"Browser Campaign {stamp}"
        page.locator('#dialogBody [name="name"]').fill(campaign_name)
        page.locator('#dialogBody [name="objective"]').fill("Browser acceptance")
        today = datetime.now().date()
        page.locator('#dialogBody [name="start_date"]').fill(today.isoformat())
        page.locator('#dialogBody [name="end_date"]').fill((today + timedelta(days=7)).isoformat())
        page.locator('#dialogBody [name="budget"]').fill("1500")
        page.locator('#dialogBody [name="channels"][value="email"]').check()
        submit_dialog(page)
        page.wait_for_function("name => document.querySelector('#content').textContent.includes(name)", arg=campaign_name)

        page.locator('[data-route="advertising"]').click()
        page.locator('#primaryAction').click()
        advert_name = f"Browser Advert {stamp}"
        page.locator('#dialogBody [name="name"]').fill(advert_name)
        page.locator('#dialogBody [name="platform"]').fill("Community directory")
        page.locator('#dialogBody [name="start_date"]').fill(today.isoformat())
        page.locator('#dialogBody [name="end_date"]').fill((today + timedelta(days=5)).isoformat())
        submit_dialog(page)
        page.wait_for_function("name => document.querySelector('#content').textContent.includes(name)", arg=advert_name)
        page.get_by_role('button', name='Advertising Opportunities').click()
        page.wait_for_function("() => document.querySelector('#pageTitle')?.textContent === 'Advertising Opportunities'")

        page.locator('[data-route="content"]').click()
        page.locator('#primaryAction').click()
        content_name = f"Browser Poster {stamp}"
        page.locator('#dialogBody [name="title"]').fill(content_name)
        page.locator('#dialogBody [name="image"]').set_input_files(str(upload))
        page.locator('#dialogBody [name="body"]').fill("Genuine uploaded campaign artwork")
        submit_dialog(page)
        page.wait_for_function("name => document.querySelector('#content').textContent.includes(name)", arg=content_name)
        assert page.locator('.library-preview img').count() >= 1

        page.locator('[data-route="email"]').click()
        page.get_by_role('button', name='Add Contact').click()
        contact_name = f"Browser Contact {stamp}"
        page.locator('#dialogBody [name="name"]').fill(contact_name)
        page.locator('#dialogBody [name="email"]').fill(f"browser-{stamp}@example.test")
        page.locator('#dialogBody [name="email_consent"]').check()
        submit_dialog(page)
        page.locator('#primaryAction').click()
        email_contacts = page.locator('#dialogBody [name="contact"] option').count()
        page.locator('#dialogBody [name="contact"]').select_option(index=email_contacts - 1)
        page.locator('#dialogBody [name="subject"]').fill("Browser scheduled email")
        page.locator('#dialogBody [name="body"]').fill("This is stored and scheduled; no provider call is made.")
        future = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
        page.locator('#dialogBody [name="scheduled_at"]').fill(future)
        page.locator('#dialogBody button[value="schedule"]').click()
        page.wait_for_function("() => !document.querySelector('#marketingDialog').open")
        page.wait_for_function("() => document.querySelector('#content').textContent.includes('Browser scheduled email')")

        page.locator('[data-route="calendar"]').click()
        page.locator('#primaryAction').click()
        activity_name = f"Browser Event {stamp}"
        page.locator('#dialogBody [name="name"]').fill(activity_name)
        page.locator('#dialogBody [name="starts_at"]').fill(future)
        submit_dialog(page)
        page.wait_for_function("name => document.querySelector('#content').textContent.includes(name)", arg=activity_name)

        page.locator('[data-route="leads"]').click()
        page.locator('#primaryAction').click()
        page.locator('#dialogBody [name="contact"]').select_option(label=contact_name)
        page.locator('#dialogBody [name="acquisition_source"]').fill("Browser campaign")
        page.locator('#dialogBody [name="received_date"]').fill(today.isoformat())
        submit_dialog(page)
        page.get_by_role('button', name='Send to CRM').last.click()
        page.wait_for_function("() => document.querySelector('#content').textContent.includes('In CRM')")

        page.locator('[data-route="analytics"]').click()
        page.locator('#primaryAction').click()
        page.locator('#dialogBody [name="reporting_date"]').fill(today.isoformat())
        page.locator('#dialogBody [name="spend"]').fill("100")
        page.locator('#dialogBody [name="reach"]').fill("1000")
        page.locator('#dialogBody [name="enquiries"]').fill("10")
        page.locator('#dialogBody [name="leads"]').fill("4")
        page.locator('#dialogBody [name="customers"]').fill("2")
        page.locator('#dialogBody [name="attributed_revenue"]').fill("400")
        submit_dialog(page)
        page.wait_for_function("() => document.querySelector('#content').textContent.includes('4×')")

        page.locator('[data-route="brand"]').click()
        page.locator('#primaryAction').click()
        business_name = f"Browser Business {stamp}"
        page.locator('#dialogBody [name="business_name"]').fill(business_name)
        page.locator('#dialogBody [name="logo"]').set_input_files(str(upload))
        submit_dialog(page)
        page.wait_for_function("name => document.querySelector('#content').textContent.includes(name)", arg=business_name)

        reader_context = browser.new_context(viewport={"width": 1200, "height": 800})
        reader_page = reader_context.new_page()
        login(reader_page, "marketing-reader-browser")
        reader_page.goto(f"{BASE_URL}/growth/#campaigns", wait_until="networkidle")
        assert reader_page.locator('#primaryAction:visible').count() == 0
        assert reader_page.locator('[data-action="edit"]').count() == 0
        reader_context.close()

        mobile_context = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile_context.new_page()
        login(mobile_page, "marketing-browser")
        mobile_page.goto(f"{BASE_URL}/growth/", wait_until="networkidle")
        mobile_page.locator('#menuButton').click()
        assert 'open' in (mobile_page.locator('#sidebar').get_attribute('class') or '')
        mobile_context.close()

        assert not page_errors, page_errors
        assert not server_errors, server_errors
        context.close()
        browser.close()
    print("PASS marketing workspace: nine routes, CRUD, genuine uploads, scheduling, CRM conversion, analytics, permissions and responsive navigation")


if __name__ == "__main__":
    run()
