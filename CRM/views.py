import json
from collections import defaultdict
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.db.models.functions import TruncDay
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.db.models import Q, Sum, Count, When, Value, CharField, Case
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from django.views import View
from django.views.generic import TemplateView, RedirectView, DetailView, DeleteView, CreateView, UpdateView, ListView

from core.enums.order_state import OrderState
from core.enums.user_enum import UserRole
from core.scripts.parser_exel_files import parse_excel
from .forms import RegistrationForm, ClientForm, ClientEditForm, OrderCreateForm, WorkerForm
from .models import Client, Order, Worker, User


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

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Order.objects.filter(Q(date_accept__icontains=query) | Q(phone__icontains=query)).order_by('id')
        else:
            return Client.objects.all().order_by('id')

    def get_context_data(self, **kwargs):
        global active_orders_worker, orders_today_worker_count, overdue_orders_worker_count, is_urgent_worker_count, waiting_pay_worker_count, sum_of_orders_worker_today
        today = date.today()
        now = datetime.now()
        context = super().get_context_data(**kwargs)
        active_orders = Order.objects.filter(state=OrderState.IN_PROGRESS.value).count()
        orders_today_count = Order.objects.filter(date_accept=today).count()
        overdue_orders_count = Order.objects.filter(
            Q(date_ready__lt=now) |
            Q(date_ready=now, date_ready__time__lt=now.time()),
            state=OrderState.IN_PROGRESS.value
        ).count()
        is_urgent_count = Order.objects.filter(is_urgent=True, state=OrderState.IN_PROGRESS.value).count()
        waiting_pay_count = Order.objects.filter(state=OrderState.COMPLETED_BUT_NOT_PAID.value).count()
        sum_of_orders_today = Order.objects.filter(date_accept=today).aggregate(total_sum=Sum('total_sum'))['total_sum']
        if sum_of_orders_today is None:
            sum_of_orders_today = 0

        if self.request.user.role == UserRole.WORKER:
            try:
                worker_profile = Worker.objects.get(user=self.request.user)
                active_orders_worker = Order.objects.filter(worker=worker_profile, state=OrderState.IN_PROGRESS.value).count()
                orders_today_worker_count = Order.objects.filter(worker=worker_profile, date_accept=today).count()
                overdue_orders_worker_count = Order.objects.filter(
                    Q(date_ready__lt=now) |
                    Q(date_ready=now, date_ready__time__lt=now.time()),
                    state=OrderState.IN_PROGRESS.value, worker=worker_profile
                ).count()
                is_urgent_worker_count = Order.objects.filter(worker=worker_profile, is_urgent=True, state=OrderState.IN_PROGRESS.value).count()
                waiting_pay_worker_count = Order.objects.filter(worker=worker_profile, state=OrderState.COMPLETED_BUT_NOT_PAID.value).count()
                sum_of_orders_worker_today = Order.objects.filter(worker=worker_profile, date_accept=today).aggregate(total_sum=Sum('total_sum'))[
                    'total_sum']
                if sum_of_orders_worker_today is None:
                    sum_of_orders_worker_today = 0
                context['active_orders_worker'] = active_orders_worker
                context['orders_today_worker_count'] = orders_today_worker_count
                context['overdue_orders_worker_count'] = overdue_orders_worker_count
                context['is_urgent_worker_count'] = is_urgent_worker_count
                context['waiting_pay_worker_count'] = waiting_pay_worker_count
                context['sum_of_orders_worker_today'] = sum_of_orders_worker_today

            except Worker.DoesNotExist:
                active_orders_worker = active_orders
                orders_today_worker_count = orders_today_count
                overdue_orders_worker_count = overdue_orders_count
                is_urgent_worker_count = is_urgent_count
                waiting_pay_worker_count = waiting_pay_count
                sum_of_orders_worker_today = sum_of_orders_today

        context['active_orders'] = active_orders
        context['orders_today_count'] = orders_today_count
        context['overdue_orders_count'] = overdue_orders_count
        context['is_urgent_count'] = is_urgent_count
        context['waiting_pay_count'] = waiting_pay_count
        context['sum_of_orders_today'] = sum_of_orders_today

        context['query'] = self.request.GET.get('q', '')  # Передаем последний запрос в контекст
        return context

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
            return Client.objects.filter(Q(full_name__icontains=query) | Q(phone__icontains=query)).order_by('id')
        else:
            return Client.objects.all().order_by('id')

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
        context['query'] = self.request.GET.get('q', '')  # Передаем последний запрос в контекст
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()

        orders = Order.objects.filter(client=client)
        active_orders = Order.objects.filter(client=client, state=OrderState.IN_PROGRESS.value)
        orders_total_sum = orders.aggregate(total_sum=Sum('total_sum'))['total_sum']
        context['orders'] = orders
        context['active_orders'] = active_orders
        context['orders_total_sum'] = orders_total_sum

        return context

    def post(self, request, *args, **kwargs):
        client = self.get_object()  # Получаем объект клиента
        notes = request.POST.get('notes')  # Получаем новые заметки из запроса

        # Обновляем заметки клиента
        client.notes = notes
        client.save()

        messages.success(request, 'Заметки успешно сохранены')

        # Возвращаем сообщение об успешном сохранении
        return HttpResponseRedirect(reverse('client_details', kwargs={'pk': client.pk}))


class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Client
    template_name = 'clients/client_delete_confirmation.html'
    success_url = reverse_lazy('clients_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        client = self.get_object()  # Получаем объект клиента
        success_url = self.get_success_url()
        self.object = client
        if success_url == self.request.path:
            messages.success(request, 'Клиент успешно удален.')
        client.delete()
        return redirect(success_url)


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
            messages.success(request, 'Все клиенты успешно удалены.')
            return redirect(self.success_url)
        else:
            messages.error(request, 'У вас нет прав для выполнения этой операции.')
            return redirect(self.success_url)


class CreateClientView(CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/new_client.html'

    def get_success_url(self):
        pk = self.object.pk
        messages.success(self.request, 'Клиент успешно добавлен')
        return reverse_lazy('client_details', kwargs={'pk': pk})


class ClientEditView(UpdateView):
    model = Client
    form_class = ClientEditForm
    template_name = 'clients/edit_client_info.html'

    def get_success_url(self):
        pk = self.object.pk
        messages.success(self.request, 'Информация о клиенте успешна изменена')
        return reverse_lazy('client_details', kwargs={'pk': pk})


class ClientOrderEditView(UpdateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'orders/update_client_order.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.object.client
        return context

    def get_success_url(self):
        pk = self.object.client.id  # Получаем id клиента, связанного с заказом
        messages.success(self.request, 'Информация о заказе успешно изменена')
        # Возвращаем URL страницы деталей клиента с использованием его id
        return reverse_lazy('client_details', kwargs={'pk': pk})


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_url'] = 'order_delete'  # URL для удаления заказа
        # Получение данных о заказах и добавление их в контекст
        orders = Order.objects.all()
        context['orders'] = orders
        return context


def import_clients(request):
    global date_check, datetime_utc
    uploaded_files = []
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('files')
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                client_data_list = parse_excel(uploaded_file)
                if client_data_list != [] and client_data_list is not None and len(client_data_list) >= 2:
                    # Проверка наличия пользователя в базе данных и создание или обновление данных
                    name = client_data_list[0]
                    try:
                        phone = client_data_list[1]
                        order_list = client_data_list[2]
                        notes = client_data_list[3]
                    except:
                        phone = ""
                        order_list = []
                        notes = []

                    try:
                        # Проверяем, существует ли пользователь с таким номером телефона
                        client = Client.objects.get(phone=phone)
                        # Если пользователь существует, обновляем его данные
                        client.full_name = name
                        client.notes = notes
                        client.save()
                        if len(order_list) > 0:
                            for order in order_list:
                                client_order = Order.objects.filter(client=client, service_name=order[0]).first()
                                if client_order:
                                    client_order.total_sum = int(order[1])
                                    client_order.notes = notes
                                    client_order.save()
                                else:
                                    date_check = order[2]
                                    if date_check is not None:
                                        try:
                                            date_obj = datetime.strptime(date_check, "%d %m %Y")
                                            date_check = date_obj.strftime("%Y-%m-%d")
                                        except Exception:
                                            date_check = order[2]
                                    Order.objects.create(
                                        date_accept=date_check,
                                        service_name=order[0],
                                        total_sum=Decimal(str(order[1])),
                                        notes=" ",
                                        client=client
                                    )

                    except Client.DoesNotExist:
                        # Если пользователь не существует, создаем нового
                        client = Client.objects.create(full_name=name, phone=phone, notes=notes)
                        for order in order_list:
                            date_check = order[2]
                            if date_check is not None:
                                try:
                                    date_obj = datetime.strptime(date_check, "%d %m %Y")
                                    date_check = date_obj.strftime("%Y-%m-%d")
                                except Exception:
                                    date_check = order[2]
                            try:
                                total_sum = order[1]
                            except Exception:
                                print("Ошибка парсинга цены")
                                total_sum = 0

                            Order.objects.create(
                                date_accept=date_check,
                                service_name=order[0],
                                total_sum=total_sum,
                                client=client,
                                notes="",
                                state=OrderState.COMPLETED.value
                            )


            else:
                continue

    clients = Client.objects.all().order_by('id')
    paginator = Paginator(clients, 100)  # Количество клиентов на странице
    page = request.GET.get('page')
    try:
        clients = paginator.page(page)
    except PageNotAnInteger:
        clients = paginator.page(1)
    except EmptyPage:
        # Если параметр страницы находится за пределами доступных страниц, выводим последнюю страницу
        clients = paginator.page(paginator.num_pages)
    if len(uploaded_files) == 0:
        messages.error(request, "Вы не выбрали файлы")
    else:
        messages.success(request, 'Клиент(ы) успешно импортированы')
    return render(request, 'clients/clients.html', {'client_objects': clients, 'clients': clients})


class ClientCreateOrder(CreateView):
    model = Client
    form_class = OrderCreateForm
    template_name = 'orders/create_client_order.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_id = self.kwargs['pk']
        client = get_object_or_404(Client, pk=client_id)
        context['client'] = client
        return context

    def get_success_url(self):
        client_id = self.kwargs['pk']
        return reverse_lazy('client_details', kwargs={'pk': client_id})

    def form_valid(self, form):
        client_id = self.kwargs['pk']
        client = get_object_or_404(Client, pk=client_id)
        form.instance.client = client
        messages.success(self.request, 'Заказ успешно создан')
        return super().form_valid(form)


class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'orders/order_delete_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.object.client
        return context

    def get_success_url(self):
        client_id = self.object.client.id
        messages.success(self.request, 'Заказ успешно удален')
        return reverse_lazy('client_details', kwargs={'pk': client_id})

    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        order.delete()

        success_url = self.get_success_url()
        return redirect(success_url)


class HistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'history/order_history.html'


class WorkersList(LoginRequiredMixin, TemplateView):
    template_name = 'workers/workers_list.html'
    context_object_name = 'workers_list'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Worker.objects.filter(Q(full_name__icontains=query) | Q(phone__icontains=query)).order_by('id')
        else:
            return Worker.objects.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workers_list = self.get_queryset()

        context['workers_list'] = workers_list
        context['query'] = self.request.GET.get('q', '')  # Передаем последний запрос в контекст
        return context


class CreateWorkerView(LoginRequiredMixin, CreateView):
    model = Worker
    form_class = WorkerForm
    template_name = 'workers/new_worker.html'
    success_url = reverse_lazy('workers_list')


class WorkerDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Worker
    template_name = 'workers/worker_delete_confirmation.html'
    success_url = reverse_lazy('workers_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        worker = self.get_object()  # Получаем объект клиента
        success_url = self.get_success_url()
        self.object = worker
        if success_url == self.request.path:
            messages.success(request, 'Работник успешно удален.')
        worker.delete()
        return redirect(success_url)


class OrderListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_str = request.GET.get('date')
        user = request.user
        if date_str:
            date = parse_date(date_str)
            if request.user.role == UserRole.WORKER:
                try:
                    worker_profile = Worker.objects.get(user=request.user)
                    orders = Order.objects.filter(worker=worker_profile, state=OrderState.IN_PROGRESS,
                                                  date_ready__date=date).order_by('date_ready')
                except Worker.DoesNotExist:
                    orders = []
            else:
                orders = Order.objects.filter(date_ready__date=date).order_by('date_ready')
        else:
            if request.user.role == UserRole.WORKER:
                try:
                    worker_profile = Worker.objects.get(user=request.user)
                    orders = Order.objects.filter(worker=worker_profile, state=OrderState.IN_PROGRESS).order_by(
                        'date_ready')
                except Worker.DoesNotExist:
                    orders = []
            else:
                orders = Order.objects.all().order_by('date_ready')

        order_list = []
        for order in orders:
            order_info = {
                'title': order.service_name,
                'id': order.id,
                'date_accept': order.date_accept.strftime("%Y-%m-%d") if order.date_accept else None,
                'start': order.date_ready.isoformat() if order.date_ready else None,
                'notes': order.notes if order.notes != 'null' else None,
                'totalSum': str(order.total_sum),
                'isUrgent': order.is_urgent,
            }

            if user.role == UserRole.OWNER and order.worker:
                order_info['worker'] = {
                    'first_name': order.worker.user.first_name,
                    'last_name': order.worker.user.last_name
                }
            order_list.append(order_info)

        return JsonResponse(order_list, safe=False)


# Dashboard


class OrderDashboardDeleteView(View):
    model = Order
    template_name = 'orders/order_delete_confirmation.html'

    def get_success_url(self):
        client_id = self.object.client.id
        messages.success(self.request, 'Заказ успешно удален')
        return reverse_lazy('dashboard')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


def delete_order(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        order.delete()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# History

class OrderHistoryByDayListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'history/order_history.html'
    context_object_name = 'orders_by_day'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Получение выбранного периода времени из GET-параметров
        period = self.request.GET.get('period', 'month')

        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'month':
            start_date = today - timedelta(days=30)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=30)  # Default to month

        if self.request.user.is_authenticated and hasattr(self.request.user, 'worker'):
            orders = Order.objects.filter(
                date_accept__range=(start_date, today),
                worker=self.request.user.worker
            )
        else:
            orders = Order.objects.filter(
                date_accept__range=(start_date, today)
            )

        sort_field = self.request.GET.get('sort', 'date_accept')
        sort_direction = self.request.GET.get('direction', 'desc')  # Default to 'desc'

        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'

        orders = orders.annotate(
            order_status=Case(
                When(state=OrderState.IN_PROGRESS.value, then=Value('1')),
                When(state=OrderState.COMPLETED.value, then=Value('2')),
                default=Value('3'),
                output_field=CharField(),
            )
        ).order_by(sort_field)

        # Группировка заказов по дням
        orders_by_day = defaultdict(list)
        for order in orders:
            orders_by_day[order.date_accept].append(order)

        # Сортировка дней в порядке убывания
        context['orders_by_day'] = sorted(orders_by_day.items(), reverse=True)
        context['selected_period'] = period

        # Проверка на наличие срочных заказов
        context['has_urgent_orders'] = any(order.is_urgent for order in orders)
        return context