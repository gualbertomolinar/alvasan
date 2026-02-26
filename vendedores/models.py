from django.db import models

# Create your models here.
class GrupoChoices(models.IntegerChoices):
    A = 1, 'Vendedoras'
    B = 2, 'Local'
    C = 3, 'Mayoristas'

class Vendedor(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.IntegerField(unique=True)
    grupo = models.IntegerField(choices=GrupoChoices.choices,default=GrupoChoices.A)

    def __str__(self):
        return f"{self.codigo} (Código: {self.nombre}, Grupo: {self.get_grupo_display()})"
