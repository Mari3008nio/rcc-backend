import os

import mysql.connector
from mysql.connector import Error

from dotenv import load_dotenv

load_dotenv()

def obtener_conexion():
    """Crea y retorna una conexión a la base de datos MySQL local."""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("MYSQLHOST"),
            port=os.getenv("MYSQLPORT"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            database=os.getenv("MYSQLDATABASE")
        )
        
        if conexion.is_connected():
            return conexion
            
    except Error as e:
        print(f"Error fatal al conectar a MySQL: {e}")
        return None