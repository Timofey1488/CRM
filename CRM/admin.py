from django.contrib import admin

from CRM.models import *

admin.site.register(User)
admin.site.register(Order)
admin.site.register(Worker)
admin.site.register(Client)

