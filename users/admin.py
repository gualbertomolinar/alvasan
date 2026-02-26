from django.contrib import admin

# Register your models here.
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'rol', 'is_superuser')
    search_fields = ('username', 'rol')