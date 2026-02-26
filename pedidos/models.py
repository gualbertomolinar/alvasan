from django.db import models

# Create your models here.
class Pedidos(models.Model):
    nroped = models.IntegerField()
    idsucur = models.IntegerField(default=1)
    iddessucur = models.CharField(max_length=40,default="")
    idcliente = models.IntegerField(default=1)
    idnomcliente = models.CharField(max_length=100, default="")
    c_perso = models.IntegerField()
    coddespercom = models.CharField(max_length=50)
    fecentre = models.DateField()
    bruto = models.DecimalField(max_digits=14, decimal_places=2)
    bonif = models.DecimalField(max_digits=14, decimal_places=2)
    netogra = models.DecimalField(max_digits=14, decimal_places=2)
    nograva= models.DecimalField(max_digits=14, decimal_places=2)
    codlipre = models.IntegerField()
    coddeslipre = models.CharField(max_length=50)
    ruta = models.IntegerField()
    coddesruta = models.CharField(max_length=50)
    iddocumento = models.CharField(max_length=6)
    dsdocumento = models.CharField(max_length=20)
    desccorta = models.CharField(max_length=15)
    idrechazo = models.IntegerField()
    preparado = models.BooleanField()
    fecalta = models.DateField()
    anulado = models.BooleanField()
    facturado = models.BooleanField()
    idmovcomercial = models.CharField(max_length=20, null=True, blank=True )
    modificado = models.BooleanField()
    total = models.DecimalField(max_digits=14, decimal_places=2)
    origen = models.CharField(max_length=30)
    pickup = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nroped', 'idsucur'], 
                name='unique_nroped'
            )
        ]

    def __str__(self):
        return f"Pedido {self.nroped} - {self.idnomcliente}"