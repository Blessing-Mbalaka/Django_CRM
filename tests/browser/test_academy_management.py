"""Playwright acceptance journey for Academy management on the live dev server."""
import os
import time

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get('CRM_TEST_BASE_URL', 'http://127.0.0.1:8023')
PASSWORD = 'JBS@2026!'


def login(page, username):
    page.goto(f'{BASE_URL}/accounts/login/', wait_until='networkidle')
    page.locator(f'[data-demo-username="{username}"]').click()
    page.get_by_role('button', name='Sign In').click()
    page.wait_for_url(f'{BASE_URL}/academy/')


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        manager = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = manager.new_page()
        page_errors, server_errors = [], []
        page.on('pageerror', lambda error: page_errors.append(str(error)))
        page.on('response', lambda response: server_errors.append(
            f'{response.status} {response.url}'
        ) if response.status >= 500 else None)
        login(page, 'ndlamini')
        page.locator('[data-route="manage"]').click()
        page.wait_for_selector('#academyManageList')
        assert page.get_by_text('ACADEMY CONTROL CENTRE').count() == 1
        for group in ('Learning', 'Resources', 'Diagnostics', 'Funding', 'Events', 'Mentorship', 'Community'):
            assert page.locator('.manage-menu h3', has_text=group).count() == 1

        page.locator('[data-manage-entity="resourceCategories"]').click()
        page.wait_for_function("() => document.querySelector('#academyManageEntityTitle')?.textContent.includes('Resource categories')")
        slug = f'playwright-{int(time.time())}'
        page.locator('[data-manage-add]').click()
        page.locator('#academyManageForm [name="name"]').fill('Playwright category')
        page.locator('#academyManageForm [name="slug"]').fill(slug)
        page.locator('#academyManageForm [name="is_active"]').check()
        page.locator('#academyManageSave').click()
        page.wait_for_function("() => !document.querySelector('#academyManageDialog').open || !document.querySelector('#academyManageErrors').hidden")
        assert not page.locator('#academyManageDialog').evaluate('dialog => dialog.open'), page.locator('#academyManageErrors').inner_text()
        page.wait_for_selector(f'.manage-row:has-text("Playwright category")')
        row = page.locator(f'.manage-row:has-text("Playwright category")')
        row.locator('[data-manage-edit]').click()
        page.locator('#academyManageForm [name="name"]').fill('Playwright category edited')
        page.locator('#academyManageSave').click()
        page.wait_for_selector('.manage-row:has-text("Playwright category edited")')
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('.manage-row:has-text("Playwright category edited") [data-manage-remove]').click()
        page.wait_for_function("() => !document.querySelector('#academyManageList')?.textContent.includes('Playwright category edited')")

        page.locator('[data-manage-entity="funding"]').click()
        page.wait_for_selector('[data-funding-import]:not([hidden])')
        assert page.locator('[data-funding-import]').is_visible()
        assert not page_errors, page_errors
        assert not server_errors, server_errors
        manager.close()

        learner = browser.new_context()
        learner_page = learner.new_page()
        login(learner_page, 'zmahlangu')
        assert learner_page.locator('[data-route="manage"]').count() == 0
        response = learner.request.get(f'{BASE_URL}/api/v1/academy/manage/courses/')
        assert response.status == 403
        learner.close()
        browser.close()
    print('PASS academy management: permissions, CRUD modal, safe removal and funding CSV entry point')


if __name__ == '__main__':
    run()
