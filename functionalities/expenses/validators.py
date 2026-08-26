from django.core.exceptions import ValidationError


def validate_vat(*, amount, vat_amount):
    if vat_amount > amount:
        raise ValidationError({'vat_amount': 'VAT amount cannot exceed the total expense.'})

