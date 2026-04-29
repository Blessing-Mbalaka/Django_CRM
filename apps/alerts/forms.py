from django import forms
from .models import Alert


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ['title', 'description', 'alert_type', 'severity', 'engagement', 'client']
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
        self.fields['engagement'].required = False
        self.fields['client'].required = False
