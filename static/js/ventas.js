/* ============================================
   FUNCIÓN GENERAL DE TOTALIZACIÓN
   ============================================ */
function totalizar(api) {

    const bloques = [
        { base: 2, utilidadCol: 6, cmgCol: 7 },
        { base: 8, utilidadCol: 12, cmgCol: 13 },
        { base: 14, utilidadCol: 18, cmgCol: 19 }
    ];

    const toDecimal = (i) =>
        typeof i === 'string' ? parseFloat(i.replace(/\,/g, '')) || 0 :
        typeof i === 'number' ? i : 0;

    bloques.forEach(b => {

        let totales = [0, 0, 0, 0];

        for (let i = 0; i < 4; i++) {
            totales[i] = api.column(b.base + i, { page: 'all' }).data()
                .reduce((a, v) => toDecimal(a) + toDecimal(v), 0);

            $(api.column(b.base + i).footer()).html(
                "<strong>" + totales[i].toLocaleString('es-ES', { minimumFractionDigits: 2 }) + "</strong>"
            );
        }

        let utilidad = totales[1] - totales[0];
        $(api.column(b.utilidadCol).footer()).html(
            "<strong>" + utilidad.toLocaleString('es-ES', { minimumFractionDigits: 2 }) + "</strong>"
        );

        let cmg = totales[1] === 0 ? 0 : (utilidad / totales[1] * 100);
        $(api.column(b.cmgCol).footer()).html(
            "<strong>" + cmg.toLocaleString('es-ES', { minimumFractionDigits: 2 }) + "</strong>"
        );
    });
}

/* ============================================
   CONFIGURACIÓN GENERAL PARA TABLAS GRANDES
   ============================================ */
function configurarTabla(selector, columnasFijas = 2) {

    return $(selector).DataTable({

        scrollX: true,
        scrollY: "600px",
        scrollCollapse: true,

        fixedHeader: {
            header: true,
            footer: true
        },

        fixedColumns: {
            leftColumns: columnasFijas
        },

        columnDefs: [
            { width: "10px", targets: 0 },
            { width: "60px", targets: 1 },
            { width: "70px", targets: "_all" },
            // Forzar orden numérico en columnas 3 a 18
            //{ type: "num-fmt", targets: [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18] }
            

        ],

        language: {
            url: "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"
        },

        footerCallback: function () {
            totalizar(this.api());
        }
    });
}

/* ============================================
   INICIALIZACIÓN DE TABLAS
   ============================================ */
$(document).ready(function () {

    // Ventas por vendedor
    configurarTabla("#ventasXvendedor", 2);

    // Ventas por localidad
    configurarTabla("#ventasXlocalidad", 2);

    // Ventas por producto
    configurarTabla("#ventasXproducto", 2);

});