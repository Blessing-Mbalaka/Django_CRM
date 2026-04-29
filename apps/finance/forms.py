from django import forms
from .models import FinancialRecord


class FinancialRecordForm(forms.ModelForm):
    class Meta:
        model = FinancialRecord
        fields = ['engagement', 'record_type', 'amount', 'description', 'date', 'is_paid']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date':        forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_paid':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
