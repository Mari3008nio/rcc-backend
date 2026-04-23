from db.conexion import obtener_conexion
from models.esquemas import ClienteBase

def obtener_todos_los_clientes():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT IdCliente as id_cliente, RazonSocial as razon_social, RFC as rfc, Contacto as contacto FROM CLIENTES")
        return cursor.fetchall()
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def crear_nuevo_cliente(cliente: ClienteBase):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO CLIENTES (RazonSocial, RFC, Contacto) VALUES (%s, %s, %s)",
            (cliente.razon_social, cliente.rfc, cliente.contacto)
        )
        conexion.commit()
        return {"mensaje": "Cliente registrado con éxito", "id_cliente": cursor.lastrowid}
    except Exception as e:
        conexion.rollback()
        return {"error": str(e)}
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def actualizar_cliente_db(id_cliente: int, cliente: ClienteBase):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE CLIENTES SET RazonSocial = %s, RFC = %s, Contacto = %s WHERE IdCliente = %s",
            (cliente.razon_social, cliente.rfc, cliente.contacto, id_cliente)
        )
        conexion.commit()
        return {"mensaje": "Cliente actualizado con éxito"}
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def eliminar_cliente_db(id_cliente: int):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        # Nota: Si el cliente ya tiene cotizaciones, MySQL bloqueará el borrado para proteger tus finanzas (Llave Foránea).
        cursor.execute("DELETE FROM CLIENTES WHERE IdCliente = %s", (id_cliente,))
        conexion.commit()
        return {"mensaje": "Cliente eliminado con éxito"}
    except Exception as e:
        conexion.rollback()
        return {"error": "No se puede borrar el cliente porque ya tiene cotizaciones guardadas."}
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()