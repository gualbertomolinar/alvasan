from django.contrib import admin

# Register your models here.
from productos.models import Productos, ListaPrecio

@admin.register(Productos)
class ProductosAdmin(admin.ModelAdmin):
    list_display = ('codart', 'descrip')
    search_fields = ('codart', 'descrip')