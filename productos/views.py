from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from concurrent.futures import ThreadPoolExecutor

from django.db import transaction 
from django.http import HttpResponse

from io import BytesIO
from datetime import datetime

import time
import pandas as pd
import numpy as np
import requests
import chardet
import csv
import io
import re


from productos.models import Productos, ListaPrecio
from .serializers import ListaUnicaSerializer

from core.permissions import TienePermisoDinamico
from core.services import sync_external_data


# Create your views here.     

class ProductosViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action == 'list':
            # Requiere estar logueado Y tener el permiso de lectura
            return [IsAuthenticated(), TienePermisoDinamico('ver_catalogo')]
        
        if self.action == 'create':
            # Requiere estar logueado Y tener permiso de escritura/carga
            return [IsAuthenticated(), TienePermisoDinamico('ver_cargar_datos')]
        
        # Para cualquier otra acción (PUT, DELETE, etc.), por defecto solo Admin 
        return [IsAdminUser()]

    def create(self, request):
        dfs = []
        tipo = request.POST.get('tipo')
        match tipo:
            case 'Catalogo':
                columnas_requeridas = ['PRODUCTO','SKU']
                mapeo = {'PRODUCTO': 'descripcat',
                         'SKU':'codart'}
                columnas_pk = ['codart']
                columnas_validas = ['codart', 'descripcat', 'posicion', 'catalogo']
            case 'Stock':
                columnas_requeridas = ['Artículo', 'Descripción artículo', 'Stock físico', 'Pendiente', 'Stock disponible']
                mapeo = {'Artículo' : 'codart',
                         'Descripción artículo': 'descrip',
                         'Stock físico':'bulto',
                         'Pendiente':'pendiente',
                         'Stock disponible':'disponible'}
                columnas_pk = ['codart']
                columnas_validas = ['codart', 'descrip', 'bulto', 'pendiente', 'disponible']
            case _:
                return Response({'error': 'Tipo no Archivo no definido'}, status=status.HTTP_400_BAD_REQUEST)
        # -----------------------------------------
        # 0. Validación del archivo recibido
        # -----------------------------------------
        
        archivo = request.FILES.get('file')
        if not archivo:
            return Response(
                {'error': 'Debe enviar un archivo en el campo "file".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        nombre = archivo.name.lower()

        # Validar extensión
        extensiones_permitidas = ('.xls', '.xlsx', '.txt', '.csv')
        if not nombre.endswith(extensiones_permitidas):
            return Response(
                {'error': 'Formato no permitido. Debe ser XLS, XLSX, TXT o CSV.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar tamaño (20 MB)
        if archivo.size > 20 * 1024 * 1024:
            return Response(
                {'error': 'El archivo supera el tamaño máximo permitido (20 MB).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # -----------------------------------------
        # 1. Lectura del archivo
        # -----------------------------------------
        # SOLO .xlsx es Excel real
        if nombre.endswith('.xlsx'):
            try:
                df_excel = pd.read_excel(
                    archivo,
                    usecols=columnas_requeridas,
                    engine='openpyxl'
                )
                dfs.append(df_excel.copy())

            except Exception as e:
                return Response(
                    {'error': f'Error al leer el archivo Excel: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # TODO LO DEMÁS → CSV/TXT (incluye .xls disfrazado)
        else:
            try:
                # Detectar encoding con muestra
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
                dfs.append(chunks.copy())

            except Exception as e:
                return Response(
                    {'error': f'Error al leer el archivo CSV/TXT: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # -----------------------------------------
        # 3. Unificación
        # -----------------------------------------
        if not dfs:
            return Response({'error': 'No hay datos válidos'}, status=status.HTTP_400_BAD_REQUEST)

        df = pd.concat(dfs, ignore_index=True)
        del dfs

        match tipo:
            case 'Catalogo':
                df['posicion'] = df.index + 1
                df['catalogo'] = True
            case 'Stock':
                print('stock')

        df.rename(columns=mapeo, inplace=True)
        df = df[columnas_validas].drop_duplicates(subset=['codart'], keep='first')
        df.to_excel(f"{tipo}.xlsx", sheet_name=f'{tipo}', index=False)
        update_fields = [c for c in columnas_validas if c not in columnas_pk]        
        registros = df.to_dict('records')
        
        instancias = [Productos(**row) for row in registros]

        with transaction.atomic():
            Productos.objects.bulk_create(
                instancias,
                batch_size=2000,
                update_conflicts=True,
                unique_fields=columnas_pk,
                update_fields=update_fields
            )

        return Response(
            {'message': f'Éxito: {len(instancias)} registros procesados.'},
            status=status.HTTP_200_OK
        )

    def list(self, request):
        return 

class ListaPrecioViewSet(viewsets.ViewSet):
    def get_permissions(self):
        """
        Mapeo de acciones a permisos específicos
        """
        # 1. ACCIÓN: Sincronizar con API externa (POST)
        if self.action == 'create':
            return [IsAuthenticated(), TienePermisoDinamico('ver_cargar_datos')]

        # 2. ACCIÓN: Ver listado para el combo/dropdown (GET)
        if self.action == 'getListas':
            return [IsAuthenticated(), TienePermisoDinamico('ver_catalogo')]

        # 3. ACCIÓN: Exportar Excel (GET)
        if self.action == 'exportar_catalogo':
            return [IsAuthenticated(), TienePermisoDinamico('exportar_excel')]

        # Por defecto, cualquier otra cosa requiere estar logueado
        return [IsAdminUser()]

 
    def create(self, request):
        try:
            total = sync_external_data()
            return Response({'status': 'success', 'items': total})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'], url_path='getListas')
    def getListas(self, request):

        listas = ListaPrecio.objects.values('idlista', 'descriplista').distinct()
        serializer = ListaUnicaSerializer(listas, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='exportarCatalogo/(?P<idlista>[^/.]+)')
    def exportar_catalogo(self, request, idlista=None):

        lista = ListaPrecio.objects.filter(idlista=idlista).first()
        descrip = lista.descriplista if lista else "lista"

        # Sanitizar
        safe_descrip = re.sub(r'[^A-Za-z0-9_-]+', '_', descrip)
        safe_sheet = safe_descrip[:31]

        fecha = datetime.now().strftime("%m-%d")
        filename = f"catalogo_{safe_descrip}_{fecha}.xlsx"


        # 1. Productos válidos
        productos = Productos.objects.filter(
            anulado=False,
            catalogo=True,
            disponible__gt=0
        ).order_by('posicion')

        # 2. Precios de la lista seleccionada
        precios = ListaPrecio.objects.filter(
            idlista=idlista,
            anulado=False,
            codart__in=productos.values('codart')
        )

        # 3. DataFrames
        df_prod = pd.DataFrame(list(productos.values(
            'codart', 'descripcat', 'marca', 'categoria',
            'undxbulto', 'disponible', 'undxbulto', 'codbarra', 'preciocomp', 'bulto', 'descrip'
        )))

        df_prec = pd.DataFrame(list(precios.values(
            'codart_id', 'preciofinal', 'precioundfinal'
        )))

        # 4. Merge
        df = df_prod.merge(df_prec, left_on='codart', right_on='codart_id', how='left')
        df.drop(columns=['codart_id'], inplace=True)

        #convertir a valores numericos
        df['preciofinal'] = pd.to_numeric(df['preciofinal'], errors='coerce').fillna(0)
        df['precioundfinal'] = pd.to_numeric(df['precioundfinal'], errors='coerce').fillna(0)
        df['preciocomp'] = pd.to_numeric(df['preciocomp'], errors='coerce').fillna(0)
        df['bulto'] = pd.to_numeric(df['bulto'], errors='coerce').fillna(0)


        # 5. Redondeo sin decimales
        df['preciofinal'] = df['preciofinal'].round(0).astype(int)
        df['precioundfinal'] = df['precioundfinal'].round(0).astype(int)
        df['preciocomp'] = df['preciocomp'].round(2).astype(int)

        # borro espacio a los lados
        df['descripcat'] = df['descripcat'].str.strip()
        df['descrip'] = df['descrip'].str.strip()

        # 6. Crear Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet(safe_sheet)
            writer.sheets[safe_sheet] = worksheet

            # --- FORMATOS ---
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D9D9D9',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            cell_format = workbook.add_format({
                'border': 1,
                'align': 'left'
            })

            codar_format = workbook.add_format({
                'border': 1,
                'align': 'right'
            })

            price_format = workbook.add_format({
                'border': 1,
                'align': 'right'
            })

            # --- ANCHO DE COLUMNAS ---
            worksheet.set_column(0, 0, 10)   # Codigo
            worksheet.set_column(1, 1, 40)   # Descripcion
            worksheet.set_column(2, 3, 15)   # Precios
            worksheet.set_column(4, 4, 20)   # Categoria
            worksheet.set_column(5, 5, 20)   # Marca
            # para odoo
            #worksheet.set_column(6, 6, 10)   # UndxBulto
            #worksheet.set_column(7, 7, 15)   # Costo
            #worksheet.set_column(8, 8, 20)   # Codigo de Barra
            #worksheet.set_column(9, 9, 10)   # Stock

            # --- ENCABEZADOS SUPERIORES ---
            worksheet.write(0, 0, "Fecha")
            worksheet.write(0, 1, datetime.now().strftime("%d-%b"))

            worksheet.write(1, 0, "Precios IVA Incluido. Sujetos a modificaciones sin previo aviso. Consulte por stock")

            # --- ENCABEZADOS DE TABLA ---
            headers = ["Codigo", "Descripcion", "Precio x Unidad", "Precio x Biulto", "Categoria", "Marca"]
            for col, h in enumerate(headers):
                worksheet.write(4, col, h, header_format)

            # --- REGISTROS DESDE FILA 6 ---
            start_row = 5
            for i, row in df.iterrows():
                worksheet.write(start_row + i, 0, row['codart'], codar_format)
                worksheet.write(start_row + i, 1, row['descrip'], cell_format)
                worksheet.write(start_row + i, 2, row['precioundfinal'], price_format)                
                worksheet.write(start_row + i, 3, row['preciofinal'], price_format)
                worksheet.write(start_row + i, 4, row['categoria'], cell_format)
                worksheet.write(start_row + i, 5, row['marca'], cell_format)
                #worksheet.write(start_row + i, 6, row['undxbulto'], price_format)
                #worksheet.write(start_row + i, 7, row['preciocomp'], cell_format)
                #worksheet.write(start_row + i, 8, row['codbarra'], cell_format)
                #worksheet.write(start_row + i, 9, row['bulto'], cell_format)



        output.seek(0)
        print(filename)
        # 7. Respuesta HTTP
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response




