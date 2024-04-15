
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from CRM.models import User
from core.enums.user_enum import UserRole


class RegistrationForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserRole.choices, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['username', 'email',  'password',  'first_name', 'last_name', 'role']
        widgets = {
            'password': forms.TextInput(attrs={'type': 'text'})  # изменяем виджет обратно на текстовый
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput()

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Данный username уже используется.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Данный email уже используется.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == UserRole.WORKER and not cleaned_data.get('phone'):
            self.add_error('phone', 'Данное поле обязательно для роли работника.')
        return cleaned_data


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)