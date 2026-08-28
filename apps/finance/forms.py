from django import forms
from .models import FinancialRecord


class FinancialRecordForm(forms.ModelForm):
    class Meta:
        model = FinancialRecord
        fields = ['engagement', 'amount', 'description', 'date']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date':        forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Pipeline amount must be greater than zero.')
        return amount

    def save(self, commit=True):
        record = super().save(commit=False)
        record.record_type = FinancialRecord.RecordType.PIPELINE
        record.is_paid = False
        if commit:
            record.save()
        return record
