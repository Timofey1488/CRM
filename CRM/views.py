from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
import requests
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView, FormView
from django_otp import match_token, devices_for_user
from django_otp.forms import OTPAuthenticationForm
from django_otp.plugins.otp_totp.models import TOTPDevice

from .forms import RegistrationForm
from .models import Client, Order


def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Дополнительные операции, связанные с ролью пользователя, могут быть добавлены здесь
            user.save()
            return redirect('login')  # Перенаправление на страницу входа после успешной регистрации
    else:
        form = RegistrationForm()
    return render(request, 'commons/signup.html', {'form': form})

class AccountLoginView(LoginView):
    template_name = 'commons/login.html'
    redirect_authenticated_user = True


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)
# Create your views here.


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/index.html'
    login_url = reverse_lazy('login')  # Укажите URL для страницы входа

    def dispatch(self, request, *args, **kwargs):
        # Проверка, авторизован ли пользователь
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)


class BusinessAnalytics(TemplateView):
    template_name = 'analitics/business_analize.html'


class ClientsList(TemplateView):
    template_name = 'clients/clients.html'


def dashboard(request):
    return render(request, 'dashboard/dashboard.html')


def import_clients(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('files')
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                break
                # Обработка данных из файла Excel
                # ...

                # Проверка наличия пользователя в базе данных и создание или обновление данных
                # for name, phone in processed_data:
                #     try:
                #         # Проверяем, существует ли пользователь с таким номером телефона
                #         client = Client.objects.get(phone=phone)
                #         # Если пользователь существует, обновляем его данные
                #         client.full_name = name
                #         client.save()
                #     except Client.DoesNotExist:
                #         # Если пользователь не существует, создаем нового
                #         client = Client.objects.create(full_name=name, phone=phone)


            else:
                return HttpResponse("Файл должен быть формата .xlsx или .xls")

        return HttpResponse("Клиенты успешно импортированы!")
    return render(request, 'import_clients.html')


# Ваша функция для обработки данных из файла Excel
def process_excel_data(file_path):
    # Пример обработки данных из файла Excel
    data = [
        {"full_name": "Иванов Иван", "phone": "1234567890", "service_name": "Услуга 1", "order_description": "Описание заказа 1", "notes": "Примечание 1", "total_sum": 100.00},
        {"full_name": "Петров Петр", "phone": "9876543210", "service_name": "Услуга 2", "order_description": "Описание заказа 2", "notes": "Примечание 2", "total_sum": 200.00},
        # Добавьте данные для других заказов
    ]
    return data

# Ваша функция для создания заказов
def create_orders_from_excel_data(data):
    for item in data:
        full_name = item["full_name"]
        phone = item["phone"]
        service_name = item["service_name"]
        order_description = item["order_description"]
        notes = item["notes"]
        total_sum = item["total_sum"]

        # Поиск клиента по имени и номеру телефона
        try:
            client = Client.objects.get(full_name=full_name, phone=phone)
        except Client.DoesNotExist:
            # Если клиент не найден, можно либо создать его, либо проигнорировать
            # Например:
            # client = Client.objects.create(full_name=full_name, phone=phone)
            continue

        # Создание заказа для найденного клиента
        order = Order.objects.create(
            service_name=service_name,
            order_description=order_description,
            notes=notes,
            total_sum=total_sum,
            client=client
        )
        # Здесь вы можете добавить дополнительную логику, если это необходимо