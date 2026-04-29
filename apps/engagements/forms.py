from django import forms
from .models import Engagement


class EngagementForm(forms.ModelForm):
    class Meta:
        model = Engagement
        fields = ['title', 'client', 'centre', 'lead_owner', 'team_members',
                  'status', 'visibility', 'start_date', 'end_date', 'last_contact', 'notes']
        widgets = {
            'start_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date':     forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'last_contact': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'team_members': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
