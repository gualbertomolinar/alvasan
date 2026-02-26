from django.contrib import admin

# Register your models here.

from .models import Vendedor
@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'grupo')
    search_fields = ('codigo', 'nombre')
