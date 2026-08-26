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

Rollback requires the pre-deployment database/media backup and the previous application build. Do not reverse financial or payroll migrations after production data has been entered without a reviewed data migration.
