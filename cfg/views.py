from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, action
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from core.services import sync_external_data, sync_pedidos_periodo, sync_ventas

class SyncViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'])
    def sincronizar(self, request):
        tareas = request.data.get('tareas', [])
        respuesta = {}

        try:
            if 'pedidos' in tareas:
                total, _, _ = sync_pedidos_periodo()
                respuesta['pedidos'] = {'total': total}

            if 'listas de precio' in tareas:
                total = sync_external_data()
                respuesta['productos'] = {'total': total}

            if 'ventas' in tareas: # Nombre que viene del componente Angular
                total_vta = sync_ventas()
                respuesta['ventas'] = {'total': total_vta}
        except Exception as e:
                return Response({'error': str(e)}, status=500)
        return Response(respuesta, status=200)
