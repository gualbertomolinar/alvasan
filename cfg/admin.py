from django.contrib import admin

# Register your models here.

from .models import Cfg
@admin.register(Cfg)
class CfgAdmin(admin.ModelAdmin):
    list_display = ('clave', 'valor')
    search_fields = ('clave',)
