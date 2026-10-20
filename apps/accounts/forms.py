from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from apps.companies.models import Company
from apps.companies.tenancy import company_context
from .models import User


class LoginForm(AuthenticationForm):
    """Styled login form with UJ accessibility attributes."""

    company = forms.SlugField(label='Company code', max_length=60, initial='original',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'organization', 'placeholder': 'Your company code'}))

    def clean(self):
        code = self.cleaned_data.get('company', '').lower()
        company = Company.objects.filter(slug=code, is_active=True).first()
        if not company:
            raise forms.ValidationError('Check your company code, username and password.')
        self.request.login_company = company
        with company_context(company):
            return super().clean()

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or email',
            'autofocus': True,
            'autocomplete': 'username',
            'aria-label': 'Username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'aria-label': 'Password',
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'job_title', 'avatar']
        widgets = {
            'first_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':       forms.TextInput(attrs={'class': 'form-control'}),
            'job_title':   forms.TextInput(attrs={'class': 'form-control'}),
        }


class UJPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class CompanyRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=200, label='Company name')
    company_code = forms.SlugField(max_length=60, label='Company code', help_text='Use this code to sign in. Letters, numbers and hyphens only.')
    email = forms.EmailField(label='Work email')

    class Meta:
        model = User
        fields = ['company_name', 'company_code', 'first_name', 'last_name', 'email', 'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_company_code(self):
        code = self.cleaned_data['company_code'].lower()
        if Company.objects.filter(slug=code).exists():
            raise forms.ValidationError('That company code is already in use.')
        return code

    def clean_username(self):
        # The new workspace has no users; other companies may use the same name.
        return self.cleaned_data['username']


class CompanyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
