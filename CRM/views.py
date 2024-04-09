from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class HomeView(TemplateView):
    template_name = 'core/index.html'


class BusinessAnalytics(TemplateView):
    template_name = 'analitics/business_analize.html'


class ClientsList(TemplateView):
    template_name = 'clients/clients.html'


