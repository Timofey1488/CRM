import base64
import io
import json
from collections import defaultdict
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.core.mail import send_mail
from django.db.models.functions import TruncDay
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.db.models import Q, Sum, Count, When, Value, CharField, Case, Avg, F
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware, now
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, RedirectView, DetailView, DeleteView, CreateView, UpdateView, ListView

from core.enums.order_state import OrderState
from core.enums.user_enum import UserRole
from core.scripts.parser_exel_files import parse_excel
from core.tools.sms_sender import sendsms
from .forms import RegistrationForm, ClientForm, ClientEditForm, OrderCreateForm, WorkerForm, WorkerEditForm
from .models import Client, Order, Worker, User
import matplotlib.pyplot as plt


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
                active_orders_worker = Order.objects.filter(worker=worker_profile,
                                                            state=OrderState.IN_PROGRESS.value).count()
                orders_today_worker_count = Order.objects.filter(worker=worker_profile, date_accept=today).count()
                overdue_orders_worker_count = Order.objects.filter(
                    Q(date_ready__lt=now) |
                    Q(date_ready=now, date_ready__time__lt=now.time()),
                    state=OrderState.IN_PROGRESS.value, worker=worker_profile
                ).count()
                is_urgent_worker_count = Order.objects.filter(worker=worker_profile, is_urgent=True,
                                                              state=OrderState.IN_PROGRESS.value).count()
                waiting_pay_worker_count = Order.objects.filter(worker=worker_profile,
                                                                state=OrderState.COMPLETED_BUT_NOT_PAID.value).count()
                sum_of_orders_worker_today = \
                    Order.objects.filter(worker=worker_profile, date_accept=today).aggregate(
                        total_sum=Sum('total_sum'))[
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
    template_name = 'analytics/business_analytics.html'


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
        next_page = self.request.GET.get('next_page')
        if next_page == '/queue/queue_orders':
            is_next_page = True
        else:
            is_next_page = False
        context['next_page'] = is_next_page
        return context

    def get_success_url(self):
        pk = self.object.client.id  # Получаем id клиента, связанного с заказом
        messages.success(self.request, 'Информация о заказе успешно изменена')

        # Получаем параметр next_page из запроса
        next_page = self.request.GET.get('next_page')
        print(next_page)
        if next_page == '/queue/queue_orders':
            return reverse_lazy('queue_orders')
        else:
            # По умолчанию возвращаемся на страницу деталей клиента
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
                                state=OrderState.TAKEN.value
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


class WorkerEditView(LoginRequiredMixin,UserPassesTestMixin, UpdateView):
    model = Worker
    template_name = 'workers/edit_worker.html'
    form_class = WorkerEditForm

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['worker'] = self.object
        return context

    def get_success_url(self):
        pk = self.object.pk
        messages.success(self.request, 'Информация о работнике успешна изменена')
        return reverse_lazy('workers_list')


class OrderListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_str = request.GET.get('date')
        user = request.user
        orders = Order.objects.filter(state__in=[OrderState.IN_PROGRESS, OrderState.PLANNED])

        if date_str:
            date = parse_date(date_str)
            if user.role == UserRole.WORKER:
                try:
                    worker_profile = Worker.objects.get(user=user)
                    orders = orders.filter(worker=worker_profile, state=OrderState.IN_PROGRESS, date_ready__date=date)
                except Worker.DoesNotExist:
                    orders = []
            else:
                orders = orders.filter(date_ready__date=date)
        else:
            if user.role == UserRole.WORKER:
                try:
                    worker_profile = Worker.objects.get(user=user)
                    orders = orders.filter(worker=worker_profile, state=OrderState.IN_PROGRESS)
                except Worker.DoesNotExist:
                    orders = []

        orders = orders.select_related('client', 'worker').order_by('date_ready').distinct()
        order_list = []
        now = timezone.now()

        for order in orders:
            is_overdue = False
            if order.date_ready:
                # Приведение order.date_ready к осведомленной дате, если она наивная
                if timezone.is_naive(order.date_ready):
                    date_ready = timezone.make_aware(order.date_ready, timezone.get_current_timezone())
                else:
                    date_ready = order.date_ready

                is_overdue = date_ready < now

            order_info = {
                'title': order.service_name,
                'id': order.id,
                'date_accept': order.date_accept.strftime("%Y-%m-%d") if order.date_accept else None,
                'start': order.date_ready.strftime("%Y-%m-%d %H:%M") if order.date_ready else None,
                'notes': order.notes if order.notes != 'null' else None,
                'totalSum': str(order.total_sum),
                'isUrgent': order.is_urgent,
                'client': order.client.full_name,
                'number': order.client.phone,
                'edit_url': reverse_lazy('client_update_order', args=[order.id]),
                'allDay': 'True',
                'isOverdue': is_overdue
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


class ClientOrderDashboardEditView(UpdateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'dashboard/update_client_order_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.object.client
        return context

    def get_success_url(self):
        return reverse_lazy('dashboard')


class ClientOrderDashboardReadyView(View):
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        if order.state == OrderState.PAID_BUT_NOT_COMPLETED:
            order.state = OrderState.COMPLETED
            order.save()
        else:
            order.state = OrderState.COMPLETED_BUT_NOT_PAID
            order.save()
        messages.success(request, "Заказ успешно выполнен")
        return redirect('dashboard')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

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


class ActiveOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/active_orders.html'
    context_object_name = 'active_orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localtime().date()

        start_of_today = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        end_of_today = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.max.time())
        )

        if self.request.user.is_authenticated and hasattr(self.request.user, 'worker'):
            orders = Order.objects.filter(
                date_ready__range=(start_of_today, end_of_today),
                worker=self.request.user.worker
            )
        else:
            orders = Order.objects.filter(
                date_ready__range=(start_of_today, end_of_today)
            )

        sort_field = self.request.GET.get('sort', 'date_ready')
        sort_direction = self.request.GET.get('direction', 'desc')  # Default to 'desc'

        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'

        orders = orders.order_by(sort_field)

        context['active_orders'] = orders

        return context


class InProgressOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/in_progress_orders.html'
    context_object_name = 'in_progress_orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated and hasattr(self.request.user, 'worker'):
            orders = Order.objects.filter(
                state=OrderState.IN_PROGRESS.value,
                worker=self.request.user.worker
            )
        else:
            orders = Order.objects.filter(
                state=OrderState.IN_PROGRESS.value,
            )

        sort_field = self.request.GET.get('sort', 'date_ready')
        sort_direction = self.request.GET.get('direction', 'desc')  # Default to 'desc'

        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'

        orders = orders.order_by(sort_field)

        context['in_progress_orders'] = orders

        return context


class UrgentOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/is_urgent_orders.html'
    context_object_name = 'urgent_orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated and hasattr(self.request.user, 'worker'):
            orders = Order.objects.filter(
                is_urgent=True,
                worker=self.request.user.worker
            )
        else:
            orders = Order.objects.filter(
                is_urgent=True,
            )

        sort_field = self.request.GET.get('sort', 'date_ready')
        sort_direction = self.request.GET.get('direction', 'desc')  # Default to 'desc'

        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'

        orders = orders.order_by(sort_field)

        context['urgent_orders'] = orders

        return context


class OverdueOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/overdue_orders.html'
    context_object_name = 'overdue_orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = datetime.now()
        if self.request.user.is_authenticated and hasattr(self.request.user, 'worker'):
            orders = Order.objects.filter(
                Q(date_ready__lt=now) |
                Q(date_ready=now, date_ready__time__lt=now.time()),
                state=OrderState.IN_PROGRESS.value,
                worker=self.request.user.worker
            )
        else:
            orders = Order.objects.filter(
                Q(date_ready__lt=now) |
                Q(date_ready=now, date_ready__time__lt=now.time()),
                state=OrderState.IN_PROGRESS.value
            )

        sort_field = self.request.GET.get('sort', 'date_ready')
        sort_direction = self.request.GET.get('direction', 'desc')  # Default to 'desc'

        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'

        orders = orders.order_by(sort_field)

        context['overdue_orders'] = orders

        return context


class WaitingPaidOrders(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/waiting_paid_orders.html'
    context_object_name = 'waiting_paid_orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'worker'):
            orders = Order.objects.filter(
                state=OrderState.COMPLETED_BUT_NOT_PAID.value,
                worker=self.request.user.worker
            )
        else:
            orders = Order.objects.filter(
                state=OrderState.COMPLETED_BUT_NOT_PAID.value
            )

        sort_field = self.request.GET.get('sort', 'date_ready')
        sort_direction = self.request.GET.get('direction', 'desc')  # Default to 'desc'

        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'

        orders = orders.order_by(sort_field)

        context['waiting_paid_orders'] = orders

        return context


# Queue


class QueueOrders(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/queue_orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated and hasattr(self.request.user, 'worker'):
            worker_profile = Worker.objects.filter(user=self.request.user).first()
            if worker_profile:
                orders = Order.objects.filter(
                    Q(state=OrderState.COMPLETED_BUT_NOT_PAID.value) | Q(state=OrderState.COMPLETED.value),
                    worker=worker_profile
                )
            else:
                orders = Order.objects.none()
        else:
            orders = Order.objects.filter(
                Q(state=OrderState.COMPLETED_BUT_NOT_PAID.value) | Q(state=OrderState.COMPLETED.value),
            )

        sort_field = self.request.GET.get('sort', 'date_ready')
        sort_direction = self.request.GET.get('direction', 'desc')  # Default to 'desc'

        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'

        orders = orders.order_by(sort_field)

        context['queue_orders'] = orders

        return context


# Send Mail on Phone


def send_mail_view(request, client_id, order_id):
    try:
        client = Client.objects.get(id=client_id)
        order = Order.objects.get(id=order_id)

        if order.state == OrderState.COMPLETED_BUT_NOT_PAID:
            sendsms(
                client.phone,
                f'{client.full_name}, ваш заказ №{order_id} - Готов. Сумма заказа {order.total_sum} руб. Спасибо что выбираете нас!',
            )
        else:
            sendsms(
                client.phone,
                f'{client.full_name}, ваш заказ №{order_id} - Готов. Спасибо что выбираете нас!',
            )
        messages.success(request, "Письмо успешно отправлено")
        order.is_notified = True
        order.save()
    except Exception as e:
        messages.error(request, f"Ошибка при отправке письма: {e}")

    return redirect('queue_orders')

# Taken Order


def take_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    order.state = OrderState.TAKEN
    order.save()
    messages.success(request, "Заказ успешно выполнен")

    return redirect('queue_orders')

# Аналитика


class BusinessAnalyticsView(TemplateView):
    template_name = 'analytics/business_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получение параметров периода из запроса
        period = self.request.GET.get('period', 'all_time')

        # Определение временных рамок для выбранного периода
        end_date = now().date()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)  # грубое приближение
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:  # all_time
            start_date = None

        # Фильтрация заказов по дате
        orders = Order.objects.all()
        if start_date:
            orders = orders.filter(date_accept__gte=start_date, date_accept__lte=end_date)

        # Агрегация данных
        total_orders = orders.count()
        total_revenue = orders.aggregate(total_revenue=Sum('total_sum'))['total_revenue'] or 0
        average_order_value = orders.aggregate(average_order_value=Avg('total_sum'))['average_order_value'] or 0
        total_urgent_orders = orders.filter(is_urgent=True).count()

        # Статистика по работникам
        worker_stats = orders.values('worker__user__first_name', 'worker__user__last_name').annotate(
            total_orders=Count('id'),
            total_revenue=Sum('total_sum')
        ).order_by('-total_revenue')

        # Объединение имени и фамилии
        worker_stats = [
            {
                'full_name': f"{stat['worker__user__first_name'] or 'Директор'} {stat['worker__user__last_name'] or ''}",
                'total_orders': stat['total_orders'],
                'total_revenue': stat['total_revenue']
            }
            for stat in worker_stats
        ]

        # Построение графика
        fig, ax = plt.subplots()
        workers = [stat['full_name'] for stat in worker_stats]
        revenues = [stat['total_revenue'] for stat in worker_stats]
        ax.bar(workers, revenues)
        ax.set_xlabel('Работники')
        ax.set_ylabel('Общая выручка')
        ax.set_title('Общая выручка по работникам')

        # Сохранение графика в буфер
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png).decode('utf-8')

        # Получение информации о клиенте месяца по сумме заказов
        top_client_by_revenue = orders.values('client__id', 'client__full_name').annotate(
            total_revenue=Sum('total_sum')
        ).order_by('-total_revenue').first()

        # Получение информации о клиенте месяца по количеству заказов
        top_client_by_orders = orders.values('client__id', 'client__full_name').annotate(total_orders=Count('id')).order_by(
            '-total_orders').first()

        context.update({
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': average_order_value,
            'total_urgent_orders': total_urgent_orders,
            'worker_stats': worker_stats,
            'graphic': graphic,
            'selected_period': period,
            'top_client_by_revenue': top_client_by_revenue,
            'top_client_by_orders': top_client_by_orders,
        })

        return context