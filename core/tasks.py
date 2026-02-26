from celery import shared_task
from .services import sync_external_data, sync_pedidos_periodo, sync_ventas
import logging

logger = logging.getLogger(__name__)

@shared_task
def sincronizacion_total_automatica():
    logger.info("Iniciando sincronización automática de fin de día...")
    
    try:
        # 1. Sincronizar Productos/Listas
        prod_count = sync_external_data()
        logger.info(f"Productos sincronizados: {prod_count}")

        # 2. Sincronizar Pedidos (últimos 2 días para asegurar)
        ped_count, _, _ = sync_pedidos_periodo(dias_atras=2)
        logger.info(f"Pedidos sincronizados: {ped_count}")

        # 3. Sincronizar Ventas (del día actual)
        vta_count = sync_ventas(dias_atras=1)
        logger.info(f"Ventas sincronizadas: {vta_count}")

    except Exception as e:
        logger.error(f"Error en la sincronización automática: {str(e)}")