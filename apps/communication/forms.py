from django import forms
from .models import CommunicationLog


class CommunicationLogForm(forms.ModelForm):
    class Meta:
        model = CommunicationLog
        fields = ['engagement', 'contact_type', 'summary', 'contact_date']
        widgets = {
            'summary':      forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'contact_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
