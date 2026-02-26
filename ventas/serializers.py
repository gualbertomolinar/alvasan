from rest_framework import serializers

from .models import VentasDetallada


class VentasSerializers(serializers.ModelSerializer):
    class Meta:
        models = VentasDetallada
        fields = ('__all__')

class DetalleVentasSerializers(serializers.ModelSerializer):
    Comprobante = serializers.CharField()
    Descripcion_Comprobante = serializers.CharField()
    Letra = serializers.CharField()
    Serie = serializers.IntegerField()
    Numero = serializers.IntegerField()
    Informado = serializers.CharField()
    Motivo_Devolucion = serializers.IntegerField()
    Descripcion_Motivo_Devolucion = serializers.CharField()
    Fecha_Comprobante = serializers.DateField()
    Sucursal = serializers.IntegerField()
    Descripcion_Sucursal = serializers.CharField()
    Vendedor = serializers.IntegerField()
    Descripcion_Vendedor = serializers.CharField()
    Numero_Pedido = serializers.IntegerField()
    Cliente = serializers.IntegerField()
    Razon_Social = serializers.CharField()
    Zona = serializers.IntegerField()
    Localidad = serializers.CharField()
    Nro_Linea = serializers.IntegerField()
    Codigo_Articulo = serializers.IntegerField()
    Descripcion_Articulo = serializers.CharField()
    Unidades_Bulto = serializers.IntegerField()
    Categorias = serializers.IntegerField()
    Descripcion_Categorias = serializers.CharField()
    Familia = serializers.IntegerField()
    Descripcion_Familia = serializers.CharField()
    Costo_Neto = serializers.DecimalField(max_digits=14, decimal_places=2)
    Bultos_Total = serializers.DecimalField(max_digits=10, decimal_places=2)
    Subtotal_Neto = serializers.DecimalField(max_digits=14, decimal_places=2)
    Subtotal_Final = serializers.DecimalField(max_digits=14, decimal_places=2)
    Canal = serializers.CharField()
    IdCanal = serializers.IntegerField()