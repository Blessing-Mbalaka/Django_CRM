from django import forms
from .models import Centre
from apps.accounts.models import User


class CentreForm(forms.ModelForm):
    class Meta:
        model = Centre
        fields = ['name', 'code', 'description', 'director', 'is_active']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control'}),
            'code':        forms.TextInput(attrs={'class': 'form-control', 'maxlength': 20}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['director'].queryset = User.objects.filter(
            role__in=('director', 'dean', 'admin'), is_active=True
        ).order_by('last_name')
        self.fields['director'].required = False
        if not self.fields['director'].widget.attrs.get('class'):
            self.fields['director'].widget.attrs['class'] = 'form-control'
