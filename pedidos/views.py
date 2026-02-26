from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, action
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from core.services import sync_pedidos_periodo


from datetime import datetime, timedelta

from pedidos.models import Pedidos



class PedidosViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def lista_pedidos(self, request):
        # Lógica para listar pedidos
        return Response({"message": "Lista de pedidos"}, status=status.HTTP_200_OK)
    

    def create(self, request):
        try:
            total, inicio, fin = sync_pedidos_periodo(dias_atras=15)
            return Response({
                "inicio": inicio, 
                "fin": fin, 
                "Registros": total
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    