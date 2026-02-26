from rest_framework import serializers
from .models import ListaPrecio, Productos

class ListaUnicaSerializer(serializers.Serializer):
    idlista = serializers.IntegerField()
    descriplista = serializers.CharField()