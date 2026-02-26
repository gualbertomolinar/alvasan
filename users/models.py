from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    # 'admin' o 'usuario'
    rol = models.CharField(max_length=20, default='usuario')
    # Guardaremos una lista: ["ver_ventas", "cargar_datos"]
    permisos = models.JSONField(default=list, blank=True)
    
