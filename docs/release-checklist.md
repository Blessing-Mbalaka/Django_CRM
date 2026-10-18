# SME Suite release checklist

Before deploying a release:

1. Set `DJANGO_SETTINGS_MODULE=jbs_crm.settings.production`.
2. Generate a unique, high-entropy `SECRET_KEY`; never reuse the development key.
3. Set `ALLOWED_HOSTS` to the deployed hostname and keep `DEBUG=False`.
4. Terminate HTTPS at a trusted proxy that sets `X-Forwarded-Proto`.
5. Run `python manage.py check --deploy --settings=jbs_crm.settings.production` and resolve every warning.
6. Back up the database and uploaded media, then run `python manage.py migrate`.
7. Run the full automated test suite and authenticated smoke checks.
8. Verify document upload/download, bank CSV import/reconciliation, invoice payment, expense approval, and payroll approval in staging.
9. Confirm only CEO/admin users can access payroll data.
10. Keep PAYE/UIF manual until versioned statutory rules have been independently verified against current SARS guidance.
11. Run `python manage.py send_due_marketing --limit 0` after migrations and configure the production scheduler with a bounded positive limit.
12. Verify `/growth/` reports provider states without exposing credential values; unconfigured channels must say **Not configured**.
13. Confirm Twilio and Meta callbacks are public HTTPS endpoints, invalid signatures return 403, and the proxy preserves the externally signed URL.
14. Test Marketing with a dedicated consented recipient only. Acceptance must not appear as delivery, and opt-outs must block provider calls.
15. Run `python tests/browser/test_marketing_workspace.py` against staging without live credentials unless a separately approved provider test is intended.

## SME workspace checks

1. Confirm `/` redirects authenticated users to `/academy/` and Business Tools links return to `/academy/#tools`.
2. Verify Tasks routes `#dashboard`, `#projects`, `#tasks`, `#my`, `#calendar`, and `#team`; upload and download an allowed attachment through its protected endpoint.
3. Confirm migrated task boards contain exactly `To Do`, `In Progress`, and `Completed`, with existing task IDs and activity retained.
4. Verify Inventory routes `#dashboard`, `#products`, `#categories`, `#in`, `#out`, `#suppliers`, `#history`, `#low`, `#reports`, and `#settings`.
5. Confirm Inventory writes/settings/backup/clear controls are visible only to CEO, Director, and System Administrator roles.
6. Download an inventory JSON backup before testing clear-data. Clear-data must preserve shared Product, Supplier, PurchaseOrder, and GoodsReceipt rows.
7. Run `.venv\Scripts\python.exe tests\browser\test_task_workspace.py` and `.venv\Scripts\python.exe tests\browser\test_inventory_workspace.py` against the development server.

Rollback requires the pre-deployment database/media backup and the previous application build. Do not reverse financial or payroll migrations after production data has been entered without a reviewed data migration.
