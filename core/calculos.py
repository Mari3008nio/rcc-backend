import datetime
from db.conexion import obtener_conexion
from models.esquemas import PeticionCotizacion

def procesar_y_guardar_cotizacion(peticion: PeticionCotizacion):
    conexion = obtener_conexion()
    if not conexion:
        return {"error": "No hay conexión a la base de datos"}

    try:
        cursor = conexion.cursor(dictionary=True)

        # --- 1. GESTIÓN DEL CLIENTE EN MYSQL ---
        # Buscamos si el cliente ya existe por su RFC
        cursor.execute("SELECT IdCliente FROM CLIENTES WHERE RFC = %s", (peticion.cliente.rfc,))
        cliente_db = cursor.fetchone()

        if cliente_db:
            id_cliente = cliente_db['IdCliente'] # Ya existe, usamos su ID
        else:
            # Es un cliente nuevo: Lo guardamos en MySQL
            contacto_full = f"{peticion.cliente.domicilio}, {peticion.cliente.ciudad}"
            cursor.execute(
                "INSERT INTO CLIENTES (RazonSocial, RFC, Contacto) VALUES (%s, %s, %s)",
                (peticion.cliente.nombre, peticion.cliente.rfc, contacto_full)
            )
            id_cliente = cursor.lastrowid # Obtenemos el ID del nuevo cliente insertado

        # --- 2. MATEMÁTICAS Y COTIZACIÓN ---
        fecha_actual = datetime.datetime.now()
        folio = f"COT-{fecha_actual.strftime('%Y%m%d-%H%M%S')}"

        subtotal = 0.0
        detalles_a_guardar = []
        datos_para_pdf = []

        for item in peticion.servicios:
            cursor.execute("SELECT Concepto, PrecioUnitario FROM CATALOGO_SERVICIOS WHERE IdServicio = %s", (item.id_servicio,))
            servicio_db = cursor.fetchone()

            if not servicio_db:
                raise Exception(f"El servicio {item.id_servicio} no existe.")

            concepto = servicio_db['Concepto']
            precio_unitario = float(servicio_db['PrecioUnitario'])
            importe_linea = precio_unitario * item.cantidad

            subtotal += importe_linea
            detalles_a_guardar.append((folio, item.id_servicio, item.cantidad, importe_linea))
            
            datos_para_pdf.append({
                "concepto": concepto, "cantidad": item.cantidad, 
                "precio_unitario": precio_unitario, "importe": importe_linea
            })

        iva = round(subtotal * 0.16, 2)
        gran_total = round(subtotal + iva, 2)

        # --- 3. GUARDADO FINAL EN MYSQL ---
        cursor.execute(
            "INSERT INTO COTIZACIONES (FolioCotizacion, IdCliente, FechaEmision, Subtotal, IVA, GranTotal) VALUES (%s, %s, %s, %s, %s, %s)",
            (folio, id_cliente, fecha_actual, subtotal, iva, gran_total)
        )
        cursor.executemany(
            "INSERT INTO DETALLES_COTIZACION (FolioCotizacion, IdServicio, Cantidad, ImporteLinea) VALUES (%s, %s, %s, %s)", 
            detalles_a_guardar
        )

        conexion.commit()

        # Mandamos TODO de vuelta para el PDF
        return {
            "exito": True,
            "folio": folio,
            "fecha": fecha_actual.strftime('%d/%m/%Y'),
            "cliente": peticion.cliente.model_dump(), # Pasamos los datos del cliente al PDF
            "finanzas": {"subtotal": subtotal, "iva": iva, "gran_total": gran_total},
            "conceptos_pdf": datos_para_pdf
        }

    except Exception as e:
        conexion.rollback()
        return {"error": str(e)}
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()