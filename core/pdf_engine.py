import os
#from xhtml2pdf import pisa
from datetime import datetime

# Configuración básica
CARPETA_SALIDA = "pdfs_generados"
CARPETA_ASSETS = "assets"

def crear_pdf_cotizacion(datos):
    """
    Recibe un diccionario con los datos de la cotización y genera un archivo PDF.
    """
    folio = datos['folio']
    nombre_archivo = f"cotizacion_{folio}.pdf"
    ruta_completa = os.path.join(CARPETA_SALIDA, nombre_archivo)

    # Asegurar que las carpetas existen
    if not os.path.exists(CARPETA_SALIDA): os.makedirs(CARPETA_SALIDA)

    # Calcular ruta absoluta del logo para que xhtml2pdf lo encuentre sin problema
    ruta_disco_logo = os.path.join(os.getcwd(), CARPETA_ASSETS, 'logo.png')
    src_logo = ruta_disco_logo if os.path.exists(ruta_disco_logo) else ""

    # --- GENERAR HTML USANDO UNA PLANTILLA ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Cotización {folio}</title>
        <style>
            @page {{
                size: letter;
                margin: 1.5cm;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 10pt;
                color: #000;
                line-height: 1.2;
            }}
            
            /* ENCABEZADO */
            .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            .logo-cell {{ width: 150px; vertical-align: middle; text-align: left; padding-bottom: 10px; }}
            .logo-img {{ width: 120px; height: auto; }}
            .brand-cell {{ vertical-align: middle; text-align: center; padding-bottom: 10px; }}
            .brand-name {{ font-size: 16pt; font-weight: bold; margin: 0; }}
            .brand-address {{ font-size: 9pt; margin-top: 5px; }}
            .hr-header {{ border-bottom: 2px solid #000; margin-bottom: 20px; }}

            /* DATOS CLIENTE Y FECHA MÁS JUNTOS */
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 11pt; table-layout: fixed; }}
            .info-table td {{ white-space: normal; word-wrap: break-word; }}
            
            /* TABLA DE CONCEPTOS */
            .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 5px; border: 2px solid #000; table-layout: fixed; }}
            .items-table th {{ background-color: #d9d9d9; font-weight: bold; text-align: center; border: 1px solid #000; padding: 5px 2px; font-size: 9pt; white-space: normal; word-wrap: break-word; }}
            .items-table td {{ border: 1px solid #000; padding: 6px 4px; text-align: center; vertical-align: middle; font-size: 9pt; white-space: normal; word-wrap: break-word; }}
            
            /* ANCHOS DE COLUMNAS FIJOS PARA EVITAR QUE SE EMPALMEN */
            .col-partida {{ width: 9%; }}
            .col-desc {{ text-align: left; width: 41%; }}
            .col-unidad {{ width: 10%; }}
            .col-cant {{ width: 10%; }}
            .col-precio {{ text-align: right; width: 15%; }}
            .col-total {{ text-align: right; width: 15%; }}

            .post-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .avisos {{ font-size: 8pt; width: 60%; vertical-align: top; }}
            .totals-table {{ width: 40%; border-collapse: collapse; border: 2px solid #000; float: right; }}
            .totals-table td {{ border: 1px solid #000; padding: 5px; text-align: right; font-size: 10pt; }}
            .label-total {{ font-weight: bold; width: 50%; }}
            .final-total {{ font-weight: bold; background-color: #d9d9d9; }}

            .footer {{ text-align: center; margin-top: 40px; font-size: 10pt; }}
        </style>
    </head>
    <body>

        <table class="header-table">
            <tr>
                <td class="logo-cell"><img src="{src_logo}" class="logo-img"></td>
                <td class="brand-cell">
                    <p class="brand-name">RC&C</p>
                    <p class="brand-name">REFRIGERACIÓN, CLIMAS Y CONSTRUCCIÓN.</p>
                    <p class="brand-address">Guadalupe Victoria #206-1, col. Emilio Portes Gil, Tampico Tamaulipas.<br>C.P. 89316<br>Tels. 833 155 19 65</p>
                </td>
            </tr>
        </table>
        <div class="hr-header"></div>

        <table class="info-table">
            <tr>
                <td style="font-weight: bold; width: 12%;">CLIENTE:</td>
                <td style="border-bottom: 1px solid #000; width: 53%;">{datos['cliente']['nombre']}</td>
                <td style="width: 5%;"></td>
                <td style="font-weight: bold; width: 10%; text-align: right; padding-right: 5px;">FECHA:</td>
                <td style="border-bottom: 1px solid #000; width: 20%; text-align: center;">{datos['fecha']}</td>
            </tr>
        </table>
        
        <div style="margin-bottom: 20px; font-size: 11pt;">
            <strong>ATENCION:</strong>
            <span style="border-bottom: 1px solid #000; display: inline-block; width: calc(100% - 75px); max-width: 100%; min-width: 0; white-space: normal; word-wrap: break-word;">{datos['cliente']['atencion']}</span>
        </div>

        <p style="text-decoration: underline; margin-bottom: 15px;">Atendiendo sus indicaciones presentamos cotización:</p>

        <table class="items-table">
            <thead>
                <tr>
                    <th class="col-partida">PARTIDA</th>
                    <th class="col-desc">DESCRIPCION</th>
                    <th class="col-unidad">UNIDAD</th>
                    <th class="col-cant">CANTIDAD</th>
                    <th class="col-precio">PRECIO UNITARIO</th>
                    <th class="col-total">TOTAL</th>
                </tr>
            </thead>
            <tbody>
    """

    # Inyectar filas
    for i, item in enumerate(datos['conceptos_pdf']):
        html_content += f"""
                <tr>
                    <td class="col-partida">{i + 1}</td>
                    <td class="col-desc">{item['concepto']}</td>
                    <td class="col-unidad">Servicio</td>
                    <td class="col-cant">{item['cantidad']}</td>
                    <td class="col-precio">${item['precio_unitario']:,.2f}</td>
                    <td class="col-total">${item['importe']:,.2f}</td>
                </tr>
        """

    # Cerrar tabla y generar totales
    html_content += f"""
            </tbody>
        </table>

        <table class="post-table">
            <tr>
                <td class="avisos">
                    PRECIOS UNITARIOS + 16% DE IVA<br>
                    PRECIOS EN MONEDA NACIONAL
                </td>
                <td style="text-align: right;">
                    <table class="totals-table">
                        <tr>
                            <td class="label-total">SUBTOTAL</td>
                            <td>${datos['finanzas']['subtotal']:,.2f}</td>
                        </tr>
                        <tr>
                            <td class="label-total">IVA (16%)</td>
                            <td>${datos['finanzas']['iva']:,.2f}</td>
                        </tr>
                        <tr>
                            <td class="label-total final-total">TOTAL</td>
                            <td class="final-total">${datos['finanzas']['gran_total']:,.2f}</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>

        <div class="footer">
            <p>SIN OTRO PARTICULAR DE MOMENTO Y AGRADECIENDO DE ANTEMANO SU ATENCION QUEDO A SUS ORDENES</p>
            <br><br><br>
            <p>ATENTAMENTE</p>
            <br><br>
            
            <table style="width: 100%;">
                <tr>
                    <td style="width: 30%;"></td>
                    <td style="width: 40%; border-top: 1px solid #000; text-align: center; padding-top: 5px; font-weight: bold;">
                        ING. SILVIA HERNÁNDEZ
                    </td>
                    <td style="width: 30%;"></td>
                </tr>
            </table>
        </div>

    </body>
    </html>
    """

    # --- CONVERTIR HTML A PDF ---
    #with open(ruta_completa, "wb") as archivo_pdf:
    #    pisa_status = pisa.CreatePDF(html_content, dest=archivo_pdf)

    #return ruta_completa if not pisa_status.err else None
    return "PDF temporalmente deshabilitado"