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
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView, FormView
from django_otp import match_token, devices_for_user
from django_otp.forms import OTPAuthenticationForm
from django_otp.plugins.otp_totp.models import TOTPDevice

from .forms import RegistrationForm

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

