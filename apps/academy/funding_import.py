import csv
import io
from dataclasses import dataclass
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import FundingOpportunity, OpportunityCategory


FUNDING_CSV_HEADERS = [
    'slug', 'title', 'provider', 'category', 'description', 'eligibility',
    'opens_on', 'closes_on', 'application_url', 'contact_email', 'is_published',
]


@dataclass
class FundingImportResult:
    rows: list
    errors: list
    imported: int = 0

    @property
    def is_valid(self):
        return not self.errors


def _optional_date(value):
    return date.fromisoformat(value) if value else None


def import_funding_csv(upload, commit=False):
    try:
        text = upload.read().decode('utf-8-sig')
    except (UnicodeDecodeError, AttributeError):
        return FundingImportResult([], [{'row': 1, 'error': 'Upload a UTF-8 CSV file.'}])
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != FUNDING_CSV_HEADERS:
        return FundingImportResult([], [{'row': 1, 'error': 'CSV headers do not match the template.'}])
    rows, errors = [], []
    categories = {item.slug: item for item in OpportunityCategory.objects.filter(is_active=True)}
    for number, raw in enumerate(reader, start=2):
        try:
            if not raw['slug'] or not raw['title'] or not raw['provider']:
                raise ValueError('slug, title and provider are required')
            category = categories.get(raw['category']) if raw['category'] else None
            if raw['category'] and not category:
                raise ValueError(f"unknown category '{raw['category']}'")
            values = {
                'slug': raw['slug'], 'title': raw['title'], 'provider': raw['provider'],
                'category': category, 'description': raw['description'], 'eligibility': raw['eligibility'],
                'opens_on': _optional_date(raw['opens_on']), 'closes_on': _optional_date(raw['closes_on']),
                'application_url': raw['application_url'], 'contact_email': raw['contact_email'],
                'is_published': raw['is_published'].strip().lower() in {'1', 'true', 'yes'},
            }
            candidate = FundingOpportunity(**values)
            candidate.full_clean(validate_unique=False)
            if candidate.opens_on and candidate.closes_on and candidate.closes_on < candidate.opens_on:
                raise ValueError('closes_on must be on or after opens_on')
            rows.append(values)
        except (ValueError, TypeError, ValidationError) as exc:
            errors.append({'row': number, 'error': str(exc)})
    result = FundingImportResult(rows, errors)
    if commit and result.is_valid:
        with transaction.atomic():
            for row in rows:
                slug = row.pop('slug')
                FundingOpportunity.objects.update_or_create(slug=slug, defaults=row)
                row['slug'] = slug
        result.imported = len(rows)
    return result
