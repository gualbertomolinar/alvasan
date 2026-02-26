from django.db import models

# Create your models here.

class VentasDetallada(models.Model):
    Comprobante = models.CharField(max_length=5)
    Descripcion_Comprobante = models.CharField(default='')
    Letra = models.CharField(max_length=1)
    Serie = models.IntegerField(default=0)
    Numero = models.IntegerField()
    Informado = models.CharField(max_length=2)
    Motivo_Devolucion = models.IntegerField()
    Descripcion_Motivo_Devolucion = models.CharField()
    Fecha_Comprobante = models.DateField()
    Sucursal = models.IntegerField()
    Descripcion_Sucursal = models.CharField()
    Vendedor = models.IntegerField()
    Descripcion_Vendedor = models.CharField()
    Numero_Pedido = models.IntegerField()
    Cliente = models.IntegerField()
    Razon_Social = models.CharField()
    Zona = models.IntegerField()
    Localidad = models.CharField()
    Nro_Linea = models.IntegerField(default=1)
    Codigo_Articulo = models.IntegerField()
    Descripcion_Articulo = models.CharField()
    Unidades_Bulto = models.IntegerField()
    Categorias = models.IntegerField()
    Descripcion_Categorias = models.CharField()
    Familia = models.IntegerField()
    Descripcion_Familia = models.CharField()
    Costo_Neto = models.DecimalField(max_digits=14, decimal_places=2)
    Bultos_Total = models.DecimalField(max_digits=10, decimal_places=2)
    Subtotal_Neto = models.DecimalField(max_digits=14, decimal_places=2)
    Subtotal_Final = models.DecimalField(max_digits=14, decimal_places=2)
    Canal = models.CharField()
    IdCanal = models.BigIntegerField(default=4)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['Comprobante', 'Letra', 'Serie', 'Numero', 'Nro_Linea', 'Codigo_Articulo'], 
                name='unique_documento_articulo'
            )
        ]