from django.db import models

# Create your models here.
class Productos(models.Model):
    codart=models.IntegerField(unique=True, primary_key=True)
    descrip=models.CharField(max_length=100, default='')
    descripcat=models.CharField(max_length=100, default='')
    marca=models.CharField(max_length=50,default='')
    categoria=models.CharField(max_length=30, default='')
    codbarra=models.CharField(max_length=16, default='')
    anulado=models.BooleanField(default=False)
    undxbulto=models.IntegerField(default=1)
    minimo=models.DecimalField(max_digits=10, decimal_places=3,default=0)
    bulto=models.DecimalField(max_digits=10, decimal_places=3,default=0)
    pendiente=models.DecimalField(max_digits=10, decimal_places=3,default=0)
    disponible=models.DecimalField(max_digits=10, decimal_places=3,default=0)
    preciocomp=models.DecimalField(max_digits=16,decimal_places=3, default=0)
    preciounicomp=models.DecimalField(max_digits=16, decimal_places=3, default=0)
    posicion=models.IntegerField(default=0)
    catalogo=models.BooleanField(default=False)

    
    def __str__(self):
        return f"{self.codart} - {self.descrip}" 

class ListaPrecio(models.Model):
    idlista=models.IntegerField()
    descriplista=models.CharField(max_length=50)
    codart=models.ForeignKey(Productos, on_delete=models.CASCADE)
    anulado=models.BooleanField(default=False)
    preciobase=models.DecimalField(max_digits=14, decimal_places=3)
    preciofinal=models.DecimalField(max_digits=14, decimal_places=4)
    precioundbase=models.DecimalField(max_digits=14, decimal_places=3)
    precioundfinal=models.DecimalField(max_digits=14, decimal_places=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['idlista', 'codart'], 
                name='unique_artxlista'
            )
        ]

    def __str__(self):
        return f"{self.idlista} - {self.descriplista}"
