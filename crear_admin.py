from passlib.context import CryptContext
from db.conexion import obtener_conexion

# Configuramos el encriptador
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# La contraseña que queremos usar
password_plano = "admin"
# Generamos el hash exacto con tu computadora
password_encriptado = pwd_context.hash(password_plano)

# Conectamos a MySQL
conexion = obtener_conexion()
cursor = conexion.cursor()

# Actualizamos a la Ing. Silvia con la contraseña correcta
cursor.execute(
    "UPDATE usuarios SET PasswordHash = %s WHERE Correo = 'admin@rcc.com'",
    (password_encriptado,)
)
conexion.commit()

print(f"¡Éxito! Contraseña actualizada.")
print(f"El hash correcto para 'admin' en tu PC es: {password_encriptado}")

cursor.close()
conexion.close()