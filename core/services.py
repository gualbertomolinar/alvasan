from django.db import transaction
from .api_client import ExternalAPIClient

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import time
import io
from datetime import datetime, timedelta

from productos.models import Productos, ListaPrecio
from pedidos.models import Pedidos
from ventas.models import VentasDetallada

import csv
import chardet

def sync_external_data():
    client = ExternalAPIClient()
    client.login() # Asegura sesión activa
    
    conf = client.config
    base_url = conf.get("Base_Url", "").rstrip('/')
    
    # 1. Obtener Lista Maestra
    url_get_list = f"{base_url}/{conf.get('url_obtenerLista')}"
    res = client.session.get(url_get_list)
    lista_maestra = res.json().get("eListaPrecios", [])
    
    # 2. Hilos para detalles
    listado_precio = []
    url_det = f"{base_url}/{conf.get('url_lista')}"
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for l in lista_maestra:
            if not l.get('anulada'):
                params = {"piLis": l['listaspre'], "piVig": l['idvigencia'], "plPre": "false", "pcFag":""}
                futures.append(executor.submit(client.fetch_detalle, url_det, params))
        for f in futures:
            listado_precio.extend(f.result())

    if not listado_precio:
        return 0

    # 3. Procesamiento Pandas
    df = pd.DataFrame(listado_precio)
    column_prod = ['codart', 'descrip', 'marca', 'codbarra', 'anulado',
                       'undxbulto', 'preciocomp', 'preciounicomp']
    column_lista = ['idlista', 'descriplista', 'codart_id', 'anulado',
                       'preciobase', 'preciofinal', 'precioundbase', 'precioundfinal']
    
    df['codart'] = pd.to_numeric(df['codart'], errors='coerce').fillna(0).astype(int)
    
    # Procesar Productos (Bulk Create/Update)
    df_prod = df.rename(columns={
        'codbarrauni': 'codbarra', 'resto': 'undxbulto',
        'precom': 'preciocomp', 'preunicom': 'preciounicomp'
    })[column_prod].drop_duplicates('codart')

    instancias_prod = [Productos(**row) for row in df_prod.to_dict('records')]
        
    # Procesar Listas
    df_lista = df.rename(columns={
        'listaspre': 'idlista', 'precio': 'preciobase',
        'titulistas': 'descriplista', 'prefin': 'preciofinal',
        'preunivta': 'precioundbase', 'codart': 'codart_id'
    })
    df_lista['precioundfinal'] = df_lista['precioundbase'] * 1.21
    df_lista = df_lista[column_lista]
    
    instancias_lista = [ListaPrecio(**row) for row in df_lista.to_dict('records')]
    # df_lista.to_excel("Listas.xlsx", sheet_name='Prod', index=False)
    # 4. Guardado Atómico
    with transaction.atomic():
        Productos.objects.bulk_create(
            instancias_prod, batch_size=2000, 
            update_conflicts=True, unique_fields=['codart'],
            update_fields=[c for c in column_prod if c != 'codart']
        )
        ListaPrecio.objects.bulk_create(
            instancias_lista, batch_size=2000,
            update_conflicts=True, unique_fields=['idlista', 'codart_id'],
            update_fields=[c for c in column_lista if c not in ['idlista', 'codart_id']]
        )

        
    return len(listado_precio)

def sync_pedidos_periodo(dias_atras=15):
    client = ExternalAPIClient()
    client.login() # Aseguramos conexión
    
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=dias_atras)
    fecha_actual = fecha_inicio

    columnas_deseadas = [
        "nroped", "idsucur", "iddessucur", "idcliente", "idnomcliente", "c_perso",
        "coddespercom", "fecentre", "bruto", "bonif", "netogra", "nograva", 
        "codlipre", "coddeslipre", "ruta", "coddesruta", "iddocumento", 
        "dsdocumento", "desccorta", "idrechazo", "preparado", "fecalta",
        "anulado", "facturado", "idmovcomercial", "modificado", "total", 
        "origen", "pickup"
    ]

    todos_los_pedidos = []

    while fecha_actual <= fecha_fin:
        str_fecha = fecha_actual.strftime("%Y-%m-%d")
        payload = {
            "dsFiltrosPedidos": {
                "eFiltros": [{
                    "estados": "", "empresas": "", "sucursales": "", "vendedores": "",
                    "filtrarxalta": "true",
                    "fechadesde": str_fecha,
                    "fechahasta": str_fecha
                }]
            }
        }

        try:
            # Usamos el cliente normalizado
            data = client.post_data("web/api/reportePedidos/obtenerPedidos", payload)
            pedidos_dia = data.get("dsPedidos", {}).get("ePedidos", [])
            
            if pedidos_dia:
                todos_los_pedidos.extend(pedidos_dia)
            
            time.sleep(0.2) # Delay pequeño para no saturar
        except Exception as e:
            print(f"Error en fecha {str_fecha}: {e}")
        
        fecha_actual += timedelta(days=1)

    if not todos_los_pedidos:
        return 0, fecha_inicio, fecha_fin

    # 1. Procesamiento con Pandas (Limpieza de datos)
    df = pd.DataFrame(todos_los_pedidos)
    df = df[columnas_deseadas].drop_duplicates(subset=['nroped', 'idsucur'])
    
    # 2. Convertir DataFrame a lista de objetos Pedidos (sin guardar aún)
    instancias_pedidos = [
        Pedidos(**row) for row in df.to_dict('records')
    ]

    # 3. Bulk Upsert (La magia de la velocidad)
    # update_conflicts=True requiere Django 4.1+ y PostgreSQL/SQLite/MySQL reciente
    with transaction.atomic():
        Pedidos.objects.bulk_create(
            instancias_pedidos,
            batch_size=500, # Procesa de a 500 para no saturar la memoria
            update_conflicts=True,
            unique_fields=['nroped', 'idsucur'], # Claves primarias/únicas
            update_fields=[col for col in columnas_deseadas if col not in ['nroped', 'idsucur']]
        )
            
    return len(instancias_pedidos), fecha_inicio, fecha_fin

def sync_ventas(dias_atras=15):
    client = ExternalAPIClient()
    client.login()
    
    hoy = datetime.now().date()
    desde = (hoy - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    hasta = hoy.strftime("%Y-%m-%d")

    payload = {
        "dsFiltrosRepCbtsVta": {
            "eFiltros": [{
                "fechadesde": desde,
                "fechahasta": hasta,
                "empresas": "1,2,4",
                "idsucur": "1,2,3",
                "tiposdoc": "DVVAA,DVVTA,FCVAA,FCVTA",
                "formasagruart": "CATEGORI,FAMILIA,MARCA,TODOS,,,,,,"
            }]
        },
        "pcTipo": "D"
    }

    # -----------------------------------------
    # 1. Columnas requeridas
    # -----------------------------------------
    columnas_requeridas = [
        'Comprobante', 'Descripcion Comprobante', 'Letra',
        'Serie \\ Punto de venta', 'Numero', 'Informado',
        'Motivo Rechazo / Devolucion', 'Descripcion Motivo Rechazo / Devolucion',
        'Fecha Comprobante', 'Sucursal', 'Descripcion Sucursal',
        'Vendedor', 'Descripcion Vendedor', 'Numero de Pedido',
        'Cliente', 'Razon Social', 'Cod. Postal', 'Localidad',
        'Nro. de Linea', 'Codigo de Articulo', 'Descripcion de Articulo',
        'Unidades por Bulto', 'CATEGORIAS', 'Descripción CATEGORIAS',
        'FAMILIA', 'Descripción FAMILIA', 'Precio de compra Neto',
        'Bultos Total', 'Subtotal Neto', 'Subtotal Final'
    ]

    dfs = []
    comprobantes_validos = ['FCVTA', 'DVVTA']
    clientes_no_validos = [
        'ABANS CONSTRUCCION S.R.L', 'ABANS PROCESOS SRL', 'BARTRADE SRL',
        'MAIN SUPPORT S.R.L.', 'MAS ACTIVOS S. A', 'SACEM S A', 'SINDAL AR SA', 'OPIFEX PRO S.R.L',
        'LEVEL TRUCK', 'NIVEL TRUCK SRL', 'FULL BENEFITS SA', 'APAHIE S.R.L'
    ]

    # 2. Pedir el reporte
    res_data = client.post_data("web/api/reporteComprobantesVta/exportarExcel", payload)
    path_archivo = res_data.get("pcArchivo")

    if not path_archivo:
        return 0

    # 3. Descargar el contenido del Excel
    archivo = client.download_file(path_archivo)
    
    # 4. Detectar encoding con muestra
    try:
                
        raw_sample = archivo.read(50000)
        det = chardet.detect(raw_sample)
        encoding_detectado = det['encoding'] or 'latin1'

        archivo.seek(0)
        raw = archivo.read()
        texto = raw.decode(encoding_detectado, errors='replace')

        # Detectar separador
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(texto[:2000])
            sep = dialect.delimiter
        except Exception:
            sep = '\t'

        archivo_io = io.StringIO(texto)

        chunks = pd.read_csv(
                    archivo_io,
                    sep=sep,
                    usecols=columnas_requeridas,
                    chunksize=30000,
                    low_memory=False
                )

        for chunk in chunks:
            mask = (
                chunk['Comprobante'].isin(comprobantes_validos) &
                ~chunk['Razon Social'].isin(clientes_no_validos)
            )
            dfs.append(chunk[mask].copy())

    except Exception as e:
       print(
            {'error': f'Error al leer el archivo CSV/TXT: {str(e)}'}
        )
       return 0

    # -----------------------------------------
    # 5. Unificación
    # -----------------------------------------
    if not dfs:
        return 0

    df = pd.concat(dfs, ignore_index=True)
    del dfs

    # -----------------------------------------
    # 6. Sanitización de datos
    # -----------------------------------------

    # 7. Normalizar Informado
    df['Informado'] = df['Informado'].astype(str).str.strip().str.upper()

    # 8. Campos enteros
    cols_int = [
        'Vendedor', 'Numero', 'Motivo Rechazo / Devolucion', 'Sucursal',
        'Numero de Pedido', 'Cliente', 'Cod. Postal', 'Nro. de Linea',
        'Codigo de Articulo', 'Unidades por Bulto', 'CATEGORIAS', 'FAMILIA'
    ]
    for col in cols_int:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # 9. Campos decimales
    cols_decimal = [
        'Precio de compra Neto', 'Bultos Total', 'Subtotal Neto', 'Subtotal Final'
    ]
    for col in cols_decimal:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # 10. Cálculos adicionales
    df['Costo_Neto'] = df['Precio de compra Neto'] * 1.21 * df['Bultos Total']
    df['Subtotal Neto'] = np.where(
        df['Informado'] == 'NO',
        df['Subtotal Final'],
        df['Subtotal Neto']
    )

    # -----------------------------------------
    # 11. Canal e IdCanal
    # -----------------------------------------
    mapa_canal = {
        'Vendedoras': [1, 3, 4, 5, 6, 11, 14, 16, 17, 18],
        'Local': [0,7],
        'Mayoristas': [9]
    }

    vendedor_to_canal = {}
    for canal, lista in mapa_canal.items():
        for v in lista:
            vendedor_to_canal[v] = canal

    df['Canal'] = df['Vendedor'].map(vendedor_to_canal).fillna('Otros')

    orden = {canal: i + 1 for i, canal in enumerate(mapa_canal.keys())}
    df['IdCanal'] = df['Canal'].map(orden).fillna(4).astype(int)

    # -----------------------------------------
    # 12. Fechas y strings
    # -----------------------------------------
    df['Fecha Comprobante'] = pd.to_datetime(
        df['Fecha Comprobante'],
        errors='coerce',
        dayfirst=True
    ).dt.date

    df['Descripcion Vendedor'] = df['Descripcion Vendedor'].fillna('Directo')
    df['Descripcion Motivo Rechazo / Devolucion'] = df[
        'Descripcion Motivo Rechazo / Devolucion'
    ].fillna('')

    # -----------------------------------------
    # 13. Mapeo final de columnas al modelo
    # -----------------------------------------
    mapeo = {
        'Descripcion Comprobante': 'Descripcion_Comprobante',
        'Serie \\ Punto de venta': 'Serie',
        'Motivo Rechazo / Devolucion': 'Motivo_Devolucion',
        'Descripcion Motivo Rechazo / Devolucion': 'Descripcion_Motivo_Devolucion',
        'Fecha Comprobante': 'Fecha_Comprobante',
        'Descripcion Sucursal': 'Descripcion_Sucursal',
        'Descripcion Vendedor': 'Descripcion_Vendedor',
        'Numero de Pedido': 'Numero_Pedido',
        'Razon Social': 'Razon_Social',
        'Cod. Postal': 'Zona',
        'Nro. de Linea': 'Nro_Linea',
        'Codigo de Articulo': 'Codigo_Articulo',
        'Descripcion de Articulo': 'Descripcion_Articulo',
        'Unidades por Bulto': 'Unidades_Bulto',
        'CATEGORIAS': 'Categorias',
        'Descripción CATEGORIAS': 'Descripcion_Categorias',
        'FAMILIA': 'Familia',
        'Descripción FAMILIA': 'Descripcion_Familia',
        'Bultos Total': 'Bultos_Total',
        'Subtotal Neto': 'Subtotal_Neto',
        'Subtotal Final': 'Subtotal_Final'
    }
    df.rename(columns=mapeo, inplace=True)

    columnas_validas = [
        f.name for f in VentasDetallada._meta.fields if f.name != 'id'
    ]
    df_final = df.reindex(columns=columnas_validas)

    # -----------------------------------------
    # 14. Bulk create con manejo de conflictos
    # -----------------------------------------
    columnas_pk = ['Comprobante', 'Letra', 'Serie', 'Numero', 'Nro_Linea', 'Codigo_Articulo']
    update_fields = [c for c in columnas_validas if c not in columnas_pk]
    registros = df_final.to_dict('records')
    instancias = [VentasDetallada(**row) for row in registros]

    with transaction.atomic():
            VentasDetallada.objects.bulk_create(
                instancias,
                batch_size=5000,
                update_conflicts=True,
                unique_fields=columnas_pk,
                update_fields=update_fields
            )

    return len(instancias)

