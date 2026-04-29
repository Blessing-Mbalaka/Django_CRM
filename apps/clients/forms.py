from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'sector', 'ownership', 'website', 'notes', 'visibility', 'centre']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in ['name', 'ownership', 'website']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
