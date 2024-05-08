from django.contrib import admin
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetView, PasswordChangeView
from django.urls import path

from CRM import views
from CRM.views import HomeView, ClientsList, dashboard, AccountLoginView, BusinessAnalytics, LogoutView, \
    registration_view, ClientDetailView, ClientDeleteView, ClientsDeleteView, CreateClientView, ClientEditView, \
    ClientCreateOrder, ClientOrderEditView, OrderDeleteView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('analytics/', BusinessAnalytics.as_view(), name='business_analytics'),
    path('import-clients/', views.import_clients, name='import_clients'),
    path('clients/', ClientsList.as_view(), name='clients_list'),
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='client_details'),
    path('clients/edit/<int:pk>/', ClientEditView.as_view(), name='client_edit_info'),
    path('clients/<int:pk>/order/', ClientCreateOrder.as_view(), name='client_create_order'),
    path('clients/<int:pk>/order_update/', ClientOrderEditView.as_view(), name='client_update_order'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    path('orders/clients/delete_order/<int:pk>', OrderDeleteView.as_view(), name='order_delete'),
    path('clients/delete_all', ClientsDeleteView.as_view(), name='clients_delete_all'),
    path('clients/create_new', CreateClientView.as_view(), name='create_client'),
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