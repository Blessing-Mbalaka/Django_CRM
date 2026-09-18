"""Playwright smoke journey for the development login accounts.

Run with:
    python tests/browser/test_dummy_users.py
"""

import os

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get('CRM_TEST_BASE_URL', 'http://127.0.0.1:8000')
PASSWORD = 'JBS@2026!'
ACCOUNTS = ('ndlamini', 'mradebe', 'zmahlangu')
SMOKE_PATHS = (
    '/', '/academy/', '/clients/', '/engagements/', '/finance/', '/analytics/',
    '/documents/', '/tasks/', '/billing/', '/expenses/', '/products/',
    '/inventory/', '/purchasing/', '/sales/', '/accounting/', '/payroll/',
    '/alerts/', '/communication/', '/staff/', '/departments/', '/system-admin/',
)
ACADEMY_SECTIONS = {
    'dashboard': 'Welcome to the SME Academy',
    'learning': 'My learning',
    'paths': 'Learning paths',
    'courses': 'Courses',
    'resources': 'Templates & resources',
    'diagnostics': 'Business diagnostics',
    'tools': 'Business tools',
    'funding': 'Funding opportunities',
    'events': 'Events & webinars',
    'mentorship': 'Mentorship',
    'community': 'Community forum',
    'growth': 'Growth',
    'certificates': 'Certificates',
}


def run():
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for username in ACCOUNTS:
            context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            page = context.new_page()
            page_errors = []
            server_errors = []
            page.on('pageerror', lambda error: page_errors.append(str(error)))
            page.on('response', lambda response: server_errors.append(
                f'{response.status} {response.url}'
            ) if response.status >= 500 else None)

            login_response = page.goto(f'{BASE_URL}/accounts/login/', wait_until='networkidle')
            assert login_response and login_response.status == 200
            assert page.locator('text=Demo accounts').count() > 0
            assert 'gradient' in page.locator('.login-wrapper').evaluate(
                "element => getComputedStyle(element).backgroundImage"
            )
            page.locator(f'[data-demo-username="{username}"]').click()
            assert page.locator('#id_username').input_value() == username
            assert page.locator('#id_password').input_value() == PASSWORD
            page.get_by_role('button', name='Sign In').click()
            page.wait_for_url(f'{BASE_URL}/academy/')
            assert page.locator('body').inner_text().strip()

            route_statuses = {}
            for path in SMOKE_PATHS:
                response = context.request.get(f'{BASE_URL}{path}', max_redirects=0)
                route_statuses[path] = response.status
                assert response.status in (200, 302, 403), f'{username} {path}: {response.status}'

            if username == 'ndlamini':
                page.goto(f'{BASE_URL}/academy/', wait_until='networkidle')
                assert page.locator('#pageTitle').inner_text() == 'Academy Dashboard'
                assert page.locator('#navigation [data-route]').count() == 14
                assert page.locator('#navigation [data-route="manage"]').count() == 1
                assert page.locator('#navigation [data-href]').count() == 3
                for section, expected_heading in ACADEMY_SECTIONS.items():
                    page.locator(f'[data-route="{section}"]').click()
                    try:
                        page.wait_for_function(
                            "heading => [...document.querySelectorAll('#academyApp h2')].some(node => node.textContent.includes(heading))",
                            arg=expected_heading,
                        )
                    except Exception as error:
                        rendered_heading = page.locator('#academyApp h2').first.inner_text()
                        raise AssertionError(
                            f'Academy route {section!r} expected {expected_heading!r}, '
                            f'rendered {rendered_heading!r}; page errors: {page_errors}'
                        ) from error
                page.locator('[data-route="tools"]').click()
                page.wait_for_selector('.academy-tool-card')
                assert page.locator('.sme-tools-banner').count() == 1
                tool_links = page.locator('.academy-tool-card a').evaluate_all(
                    "links => links.map(link => link.getAttribute('href'))"
                )
                assert tool_links
                assert all('127.0.0.1' not in link for link in tool_links)
                page.goto(f'{BASE_URL}/billing/', wait_until='networkidle')
                assert 'sme-branded-app' in page.locator('body').get_attribute('class')
                assert page.get_by_role('link', name='Back to Business Tools').get_attribute('href') == '/academy/#tools'
                assert not page.locator('#invoiceModal').is_visible()
                stat_positions = page.locator('.stat-card').evaluate_all(
                    "cards => cards.slice(0, 4).map(card => Math.round(card.getBoundingClientRect().top))"
                )
                assert len(stat_positions) == 4
                assert max(stat_positions) - min(stat_positions) <= 2

            page.goto(f'{BASE_URL}/', wait_until='networkidle')
            assert page.locator('.sme-tool-icon').count() >= 26
            assert page.locator('a[href="/academy/#diagnostics"]').count() == 1
            logout = page.locator('form.sme-quick-logout button')
            assert logout.count() == 1
            logout.click()
            page.wait_for_url(f'{BASE_URL}/accounts/login/')
            assert not page_errors, f'{username} page errors: {page_errors}'
            assert not server_errors, f'{username} server errors: {server_errors}'
            results.append((username, route_statuses))
            context.close()
        browser.close()

    for username, statuses in results:
        status_summary = ', '.join(f'{path}={status}' for path, status in statuses.items())
        print(f'PASS {username}: {status_summary}')


if __name__ == '__main__':
    run()
