"""
URL configuration for atelierCRM project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetView, PasswordChangeView
from django.urls import path, include
from django.conf.urls.static import static

from CRM import views
from CRM.views import HomeView, ClientsList, dashboard, AccountLoginView, BusinessAnalytics, LogoutView, \
    registration_view, ClientDetailView, ClientDeleteView, ClientsDeleteView
from atelierCRM import settings

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('analytics/', BusinessAnalytics.as_view(), name='business_analytics'),
    path('import-clients/', views.import_clients, name='import_clients'),
    path('clients/', ClientsList.as_view(), name='clients_list'),
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='client_details'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    path('clients/delete/all', ClientsDeleteView.as_view(), name='clients_delete_all'),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', AccountLoginView.as_view(), name='login'),
    path(
        "logout/", LogoutView.as_view(),
        name="user_logout"
    ),
    path('register/', registration_view, name='register'),
    path(
            'change-password/',
            PasswordChangeView.as_view(
                template_name='commons/password_change.html',
                success_url='/'
            ),
            name='change_password'
    ),

        # Forget Password
        path('password-reset/',
             PasswordResetView.as_view(
                 template_name='commons/password-reset/password_reset.html',
                 subject_template_name='commons/password-reset/password_reset_subject.txt',
                 success_url='/login/'
             ),
             name='password_reset'),
        path('password-reset/done/',
             PasswordResetDoneView.as_view(
                 template_name='commons/password-reset/password_reset_done.html'
             ),
             name='password_reset_done'),
        path('password-reset-confirm/<uidb64>/<token>/',
             PasswordResetConfirmView.as_view(
                 template_name='commons/password-reset/password_reset_confirm.html'
             ),
             name='password_reset_confirm'),
        path('password-reset-complete/',
             PasswordResetCompleteView.as_view(
                 template_name='commons/password-reset/password_reset_complete.html'
             ),
             name='password_reset_complete'),

]