"""Playwright acceptance journey for the database-backed inventory workspace."""
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
    stamp = str(int(time.time()))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        page = context.new_page()
        page_errors, server_errors = [], []
        page.on('pageerror', lambda error: page_errors.append(str(error)))
        page.on('response', lambda response: server_errors.append(f'{response.status} {response.url}') if response.status >= 500 else None)
        login(page)
        page.goto(f'{BASE_URL}/inventory/', wait_until='networkidle')
        page.wait_for_selector('[data-route="dashboard"].active')
        assert page.locator('#navigation [data-route]').count() == 10
        expected = {'dashboard':'Dashboard','products':'Products','categories':'Categories','in':'Stock In','out':'Stock Out','suppliers':'Suppliers','history':'Stock History','low':'Low Stock','reports':'Reports','settings':'Settings'}
        for route, title in expected.items():
            page.locator(f'[data-route="{route}"]').click()
            page.wait_for_function("value => document.querySelector('#pageTitle')?.textContent === value", arg=title)

        page.locator('[data-route="categories"]').click(); page.get_by_role('button', name='＋ Add Category').first.click()
        category_name = f'Browser Category {stamp}'
        page.locator('#modalBody [name="name"]').fill(category_name)
        page.locator('#modalBody [type="submit"]').click()
        page.wait_for_function("name => document.querySelector('#content')?.textContent.includes(name)", arg=category_name)

        page.locator('[data-route="suppliers"]').click(); page.get_by_role('button', name='＋ Add Supplier').first.click()
        supplier_name = f'Browser Supplier {stamp}'
        page.locator('#modalBody [name="name"]').fill(supplier_name)
        page.locator('#modalBody [name="email"]').fill(f'browser-{stamp}@example.com')
        page.locator('#modalBody [type="submit"]').click()
        page.wait_for_function("name => document.querySelector('#content')?.textContent.includes(name)", arg=supplier_name)

        page.locator('[data-route="products"]').click(); page.get_by_role('button', name='＋ Add Product').first.click()
        product_name, sku = f'Browser Product {stamp}', f'BROWSER-{stamp}'
        page.locator('#modalBody [name="name"]').fill(product_name)
        page.locator('#modalBody [name="sku"]').fill(sku)
        page.locator('#modalBody [name="category"]').select_option(label=category_name)
        page.locator('#modalBody [name="preferred_supplier"]').select_option(label=supplier_name)
        page.locator('#modalBody [name="cost_price"]').fill('10.00')
        page.locator('#modalBody [name="sales_price"]').fill('15.00')
        page.locator('#modalBody [type="submit"]').click()
        page.wait_for_function("name => document.querySelector('#content')?.textContent.includes(name)", arg=product_name)

        page.locator('[data-route="in"]').click()
        page.locator('#content [name="product"]').select_option(label=product_name)
        page.locator('#content [name="location"]').select_option(index=1)
        page.locator('#content [name="quantity"]').fill('5')
        page.locator('#content [name="unit_cost"]').fill('10')
        page.locator('#content [type="submit"]').click()
        page.wait_for_selector('#workspaceStatus:not([hidden])')

        page.locator('[data-route="out"]').click()
        page.locator('#content [name="product"]').select_option(label=product_name)
        page.locator('#content [name="location"]').select_option(index=1)
        page.locator('#content [name="quantity"]').fill('2')
        page.locator('#content [type="submit"]').click()
        page.wait_for_selector('#workspaceStatus:not([hidden])')

        page.locator('[data-route="history"]').click()
        assert page.get_by_text(product_name).count() >= 1
        page.locator('[data-route="reports"]').click()
        for name in ('Current Stock Summary','Inventory Value','Low Stock Report','Out of Stock Report','Stock Movement Summary','Products by Category'):
            page.get_by_role('button', name=name).click()
            page.wait_for_function("name => document.querySelector('.panel h2')?.textContent === name", arg=name)
        with page.expect_download() as download_info:
            page.get_by_role('button', name='Export CSV').click()
        assert download_info.value.suggested_filename == 'inventory-report.csv'

        page.locator('[data-route="settings"]').click()
        business_name = page.locator('#content [name="business_name"]').input_value()
        page.locator('#content [type="submit"]').click()
        page.wait_for_selector('#workspaceStatus:not([hidden])')
        assert page.locator('#businessName').inner_text() == business_name

        reader = browser.new_context(); reader_page = reader.new_page(); login(reader_page, 'zmahlangu')
        reader_page.goto(f'{BASE_URL}/inventory/#products', wait_until='networkidle')
        assert reader_page.locator('[data-action="add-product"]').count() == 0
        reader_page.locator('[data-route="settings"]').click()
        assert reader_page.locator('[data-action="clear-data"]').count() == 0
        reader.close()

        mobile = browser.new_context(viewport={'width': 390, 'height': 844}); mobile_page = mobile.new_page(); login(mobile_page)
        mobile_page.goto(f'{BASE_URL}/inventory/', wait_until='networkidle'); mobile_page.locator('#menuButton').click()
        assert 'mobile-open' in mobile_page.locator('#sidebar').get_attribute('class')
        assert not page_errors, page_errors
        assert not server_errors, server_errors
        mobile.close(); context.close(); browser.close()
    print('PASS inventory workspace: ten routes, CRUD, stock flow, reports, permissions and responsive navigation')


if __name__ == '__main__':
    run()
