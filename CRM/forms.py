from datetime import datetime

from django.utils import timezone, formats

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from CRM.models import User, Client, Order, Worker
from core.enums.order_state import OrderState
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


class ClientEditForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name', 'phone']
        labels = {
            'full_name': 'Full Name',
            'phone': 'Phone Number'
        }
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance')
            if instance:
                kwargs['initial'] = {
                    'full_name': instance.full_name,
                    'phone': instance.phone,
                }
            super().__init__(*args, **kwargs)


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name', 'phone']
        labels = {
            'full_name': 'Full Name',
            'phone': 'Phone Number'
        }
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone = ''.join(filter(str.isdigit, phone))
        # Если номер начинается с "80", заменяем его на "+375"
        if phone.startswith('80'):
            phone = '375' + phone[2:]
        # Разбиваем номер телефона на части с использованием разделителей
        formatted_phone = f"+{phone[:3]}({phone[3:5]}){phone[5:8]}-{phone[8:10]}-{phone[10:]}"

        # Проверяем, существует ли пользователь с таким номером телефона
        if Client.objects.filter(phone=formatted_phone).exists():
            raise forms.ValidationError('Пользователь с таким номером телефона уже существует.')
        return formatted_phone


class OrderCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OrderCreateForm, self).__init__(*args, **kwargs)

        # Создаем список выборов для состояния заказа
        choices = [(state.value, state.value) for state in OrderState if
                   state in [OrderState.PLANNED, OrderState.IN_PROGRESS, OrderState.COMPLETED,
                             OrderState.COMPLETED_BUT_NOT_PAID]]

        # Устанавливаем выборы для поля состояния
        self.fields['state'].choices = choices

        instance = kwargs.get('instance')
        if instance and instance.date_accept:
            self.initial['date_accept'] = instance.date_accept.strftime('%Y-%m-%d')
        else:
            self.initial['date_accept'] = datetime.now().strftime('%Y-%m-%d')

        if instance and instance.date_ready:
            self.initial['date_ready'] = instance.date_ready.strftime('%Y-%m-%d %H:%M:%S')


    class Meta:
        model = Order
        fields = ['date_accept', 'date_ready', 'service_name', 'notes', 'total_sum', 'state', 'is_urgent']
        labels = {
            'date_accept': 'Дата принятия',
            'date_ready': 'Дата готовности',
            'service_name': 'Название услуги',
            'notes': 'Заметки',
            'total_sum': 'Сумма заказа',
            'state': 'Статус',
            'is_urgent': 'Срочный',
        }
        widgets = {
            'date_accept': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_ready': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'service_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'total_sum': forms.NumberInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-indigo-600'}),
        }
        required = {
            'notes': False,
        }


    def clean_notes(self):
        notes = self.cleaned_data.get('notes')
        if notes is None:
            return ''
        return notes


class WorkerForm(forms.ModelForm):
    # Поля пользователя
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    first_name = forms.CharField(label='Имя', max_length=30)
    last_name = forms.CharField(label='Фамилия', max_length=30)

    # Поля работника
    phone = forms.CharField(label='Телефон', max_length=15)
    position = forms.CharField(label='Должность', max_length=30)
    hire_date = forms.DateField(label='Дата найма')

    class Meta:
        model = Worker
        fields = ['phone', 'position', 'hire_date']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Это имя пользователя уже занято.")
        return username

    def save(self, commit=True):
        # Сохранение пользователя
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            role=UserRole.WORKER,
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        # Сохранение работника
        worker = super().save(commit=False)
        worker.user = user
        if commit:
            worker.save()
        return worker


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)
