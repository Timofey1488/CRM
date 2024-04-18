from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
import requests
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView, FormView, ListView, DetailView, DeleteView
from django_otp import match_token, devices_for_user
from django_otp.forms import OTPAuthenticationForm
from django_otp.plugins.otp_totp.models import TOTPDevice

from core.scripts.parser_exel_files import parse_excel
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


class ClientsList(LoginRequiredMixin, TemplateView):
    template_name = 'clients/clients.html'
    context_object_name = 'clients'
    paginate_by = 100  # Количество клиентов на странице

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Client.objects.filter(Q(full_name__icontains=query) | Q(phone__icontains=query))
        else:
            return Client.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients_list = self.get_queryset()
        paginator = Paginator(clients_list, self.paginate_by)
        page = self.request.GET.get('page')
        try:
            clients = paginator.page(page)
        except PageNotAnInteger:
            # Если параметр страницы не является целым числом, выводим первую страницу
            clients = paginator.page(1)
        except EmptyPage:
            # Если параметр страницы находится за пределами доступных страниц, выводим последнюю страницу
            clients = paginator.page(paginator.num_pages)

        context['clients'] = clients
        context['client_objects'] = clients.object_list
        print(f"client_list: {clients.object_list}")
        context['query'] = self.request.GET.get('q', '')  # Передаем последний запрос в контекст
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'


class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Client
    template_name = 'clients/client_delete_confirmation.html'
    success_url = reverse_lazy('clients_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        client = get_object_or_404(Client, pk=self.kwargs['pk'])  # Получаем объект клиента по переданному идентификатору
        client.delete()  # Удаляем только этого клиента
        messages.success(request, 'Клиент успешно удален.')
        return super().delete(request, *args, **kwargs)


class ClientsDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    model = Client
    template_name = 'clients/clients_delete_all_confirmation.html'
    success_url = reverse_lazy('clients_list')

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        if self.request.user.is_staff:
            Client.objects.all().delete()  # Удаляем всех клиентов
            messages.success(self.request, 'Все клиенты успешно удалены.')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'У вас нет прав для выполнения этой операции.')
            return redirect(self.success_url)


def dashboard(request):
    return render(request, 'dashboard/dashboard.html')


def import_clients(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('files')
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                client_data_list = parse_excel(uploaded_file)
                if client_data_list is not None and len(client_data_list) >= 2:
                    # Проверка наличия пользователя в базе данных и создание или обновление данных
                    name = client_data_list[0]
                    phone = client_data_list[1]

                    # Здесь выполняется код для обработки каждой пары (name, phone)
                    print("Имя:", name)
                    print("Телефон:", phone)
                    try:
                        # Проверяем, существует ли пользователь с таким номером телефона
                        client = Client.objects.get(phone=phone)
                        # Если пользователь существует, обновляем его данные
                        client.full_name = name
                        client.save()
                    except Client.DoesNotExist:
                        # Если пользователь не существует, создаем нового
                        Client.objects.create(full_name=name, phone=phone)

            else:
                return HttpResponse("Файл должен быть формата .xlsx или .xls")
    clients = Client.objects.all()

    return render(request, 'clients/clients.html', {'clients': clients})


def search_view(request):
    query = request.GET.get('q', '')  # Получаем значение из параметра запроса 'q'
    results = Client.objects.filter(Q(full_name__icontains=query) | Q(phone__icontains=query))
    return render(request, 'clients/clients.html', {'results': results, 'query': query})

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
