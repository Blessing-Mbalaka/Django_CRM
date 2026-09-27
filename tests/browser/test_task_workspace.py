"""Playwright acceptance journey for the database-backed task workspace."""
import os
import time

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get('CRM_TEST_BASE_URL', 'http://127.0.0.1:8023')


def login(page, username='ndlamini'):
    page.goto(f'{BASE_URL}/accounts/login/', wait_until='networkidle')
    page.locator(f'[data-demo-username="{username}"]').click()
    page.get_by_role('button', name='Sign In').click()
    page.wait_for_url(f'{BASE_URL}/academy/')


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        page_errors, server_errors = [], []
        page.on('pageerror', lambda error: page_errors.append(str(error)))
        page.on('response', lambda response: server_errors.append(f'{response.status} {response.url}') if response.status >= 500 else None)
        login(page)
        page.goto(f'{BASE_URL}/tasks/', wait_until='networkidle')
        page.wait_for_selector('[data-route="dashboard"].active')
        assert page.locator('#navigation [data-route]').count() == 6
        expected = {'dashboard':'Task & Project Management','projects':'Projects','tasks':'Tasks','my':'My Tasks','calendar':'Calendar','team':'Team'}
        for route, title in expected.items():
            page.locator(f'[data-route="{route}"]').click()
            page.wait_for_function("value => document.querySelector('#pageTitle')?.textContent === value", arg=title)

        page.locator('[data-route="projects"]').click()
        page.locator('#primaryAction').click()
        prefix = f'Browser project {int(time.time())}'
        page.locator('#modalBody [name="name"]').fill(prefix)
        page.locator('#modalBody [name="status"]').select_option('active')
        page.locator('#modalBody [type="submit"]').click()
        page.wait_for_function("name => document.querySelector('#content')?.textContent.includes(name)", arg=prefix)

        page.locator('[data-route="tasks"]').click()
        page.locator('#primaryAction').click()
        task_name = f'Browser task {int(time.time())}'
        page.locator('#modalBody [name="title"]').fill(task_name)
        page.locator('#modalBody [name="assignee"]').select_option(index=1)
        page.locator('#modalBody [type="submit"]').click()
        page.wait_for_function("name => document.querySelector('#content')?.textContent.includes(name)", arg=task_name)

        mobile = browser.new_context(viewport={'width': 390, 'height': 844})
        mobile_page = mobile.new_page(); login(mobile_page)
        mobile_page.goto(f'{BASE_URL}/tasks/', wait_until='networkidle')
        mobile_page.locator('#menuButton').click()
        assert 'open' in mobile_page.locator('#sidebar').get_attribute('class')
        assert not page_errors, page_errors
        assert not server_errors, server_errors
        mobile.close(); context.close(); browser.close()
    print('PASS task workspace: routes, project/task persistence and responsive navigation')


if __name__ == '__main__':
    run()
