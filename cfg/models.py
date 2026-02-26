from django.db import models

# Create your models here.

class Cfg(models.Model):
    clave = models.CharField(max_length=20, unique=True)
    valor = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.clave}"
