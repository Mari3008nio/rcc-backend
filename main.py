from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import random
import os

from core.pdf_engine import crear_pdf_cotizacion
from db.conexion import obtener_conexion

# --- SEGURIDAD ---
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError

app = FastAPI(title="API RC&C - Climas y Construcción")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("pdfs_generados"):
    os.makedirs("pdfs_generados")
app.mount("/pdfs", StaticFiles(directory="pdfs_generados"), name="pdfs")

if not os.path.exists("assets"):
    os.makedirs("assets")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD (JWT)
# ==========================================
SECRET_KEY = "tu_clave_secreta_rcc_muy_segura_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

def verificar_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def crear_token_acceso(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

def construir_url_pdf(folio: str, request: Request) -> str:
    """Construye la URL correcta del PDF usando el host actual."""
    # Obtener protocolo y host del request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8000"))
    return f"{scheme}://{host}/pdfs/cotizacion_{folio}.pdf"


@app.post("/api/v1/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error de BD")
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE Correo = %s AND EstadoActivo = 1", (form_data.username,))
        usuario = cursor.fetchone()

        if not usuario or not verificar_password(form_data.password, usuario['PasswordHash']):
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

        token = crear_token_acceso(data={"sub": usuario['Correo'], "nombre": usuario['NombreCompleto']})
        return {"access_token": token, "token_type": "bearer", "nombre": usuario['NombreCompleto']}
    finally:
        cursor.close()
        conexion.close()


# --- MODELOS PYDANTIC ---
class ServicioCotizacion(BaseModel):
    concepto: str
    precio_unitario: float
    cantidad: int
class ClienteCotizacion(BaseModel):
    id_cliente: int
    nombre: str
    atencion: str  
class PeticionCotizacion(BaseModel):
    cliente: ClienteCotizacion
    servicios: List[ServicioCotizacion]
class ClienteNuevo(BaseModel):
    nombre: str
    atencion: str
    telefono: str
    domicilio: str
    rfc: str
class ClienteActualizar(BaseModel):
    id_cliente: int
    nombre: str
    atencion: str
    telefono: str
    domicilio: str
    rfc: str
class ServicioNuevo(BaseModel):
    concepto: str
    precio_unitario: float
class ServicioActualizar(BaseModel):
    id_servicio: int
    concepto: str
    precio_unitario: float


# ==========================================
# RUTAS DE CLIENTES
# ==========================================
@app.post("/api/v1/clientes/guardar")
async def guardar_cliente(cliente: ClienteNuevo, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor()
        consulta = "INSERT INTO clientes (RazonSocial, RFC, Contacto, Telefono, Domicilio, EstadoActivo) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(consulta, (cliente.nombre, cliente.rfc, cliente.atencion, cliente.telefono, cliente.domicilio, 1))
        conexion.commit()
        return {"mensaje": "Cliente guardado", "id": cursor.lastrowid}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.put("/api/v1/clientes/actualizar")
async def actualizar_cliente(cliente: ClienteActualizar, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor()
        consulta = "UPDATE clientes SET RazonSocial = %s, RFC = %s, Contacto = %s, Telefono = %s, Domicilio = %s WHERE IdCliente = %s"
        cursor.execute(consulta, (cliente.nombre, cliente.rfc, cliente.atencion, cliente.telefono, cliente.domicilio, cliente.id_cliente))
        conexion.commit()
        return {"mensaje": "Cliente actualizado"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/api/v1/clientes/listar")
async def listar_clientes(usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT IdCliente AS id, RazonSocial AS nombre, Contacto AS atencion, Telefono AS telefono, Domicilio AS domicilio, RFC AS rfc FROM clientes WHERE EstadoActivo = 1 ORDER BY RazonSocial ASC")
        return {"clientes": cursor.fetchall()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.delete("/api/v1/clientes/borrar/{id_cliente}")
async def borrar_cliente(id_cliente: int, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM clientes WHERE IdCliente = %s", (id_cliente,))
        conexion.commit()
        return {"mensaje": "Cliente borrado"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()


# ==========================================
# RUTAS DEL CATÁLOGO DE SERVICIOS
# ==========================================
@app.get("/api/v1/servicios/listar")
async def listar_servicios(usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT IdServicio AS id, Concepto AS descripcion, PrecioUnitario AS precio FROM catalogo_servicios WHERE EstadoActivo = 1 ORDER BY Concepto ASC")
        return {"servicios": cursor.fetchall()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.post("/api/v1/servicios/guardar")
async def guardar_servicio(servicio: ServicioNuevo, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor()
        consulta = "INSERT INTO catalogo_servicios (Concepto, PrecioUnitario, TipoServicio, EstadoActivo) VALUES (%s, %s, %s, %s)"
        cursor.execute(consulta, (servicio.concepto, servicio.precio_unitario, 'Servicio', 1))
        conexion.commit()
        return {"mensaje": "Servicio guardado", "id": cursor.lastrowid}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.put("/api/v1/servicios/actualizar")
async def actualizar_servicio(servicio: ServicioActualizar, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor()
        consulta = "UPDATE catalogo_servicios SET Concepto = %s, PrecioUnitario = %s WHERE IdServicio = %s"
        cursor.execute(consulta, (servicio.concepto, servicio.precio_unitario, servicio.id_servicio))
        conexion.commit()
        return {"mensaje": "Servicio actualizado"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.delete("/api/v1/servicios/borrar/{id_servicio}")
async def borrar_servicio(id_servicio: int, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error BD")
    try:
        cursor = conexion.cursor()
        cursor.execute("UPDATE catalogo_servicios SET EstadoActivo = 0 WHERE IdServicio = %s", (id_servicio,))
        conexion.commit()
        return {"mensaje": "Servicio desactivado"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()


# ==========================================
# RUTAS DE COTIZACIONES (COTIZACIÓN LIBRE)
# ==========================================
@app.post("/api/v1/cotizaciones/generar")
async def generar_cotizacion(peticion: PeticionCotizacion, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error de BD")
    try:
        cursor = conexion.cursor(dictionary=True)
        
        subtotal = 0.0
        conceptos_pdf = []
        detalles_a_guardar = []
        folio_generado = f"COT-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"

        for serv in peticion.servicios:
            importe = serv.precio_unitario * serv.cantidad
            subtotal += importe
            
            conceptos_pdf.append({
                "concepto": serv.concepto,
                "cantidad": serv.cantidad,
                "precio_unitario": serv.precio_unitario,
                "importe": importe
            })

            # BUSCAR SI EXISTE EXACTAMENTE ESE CONCEPTO Y PRECIO
            cursor.execute("SELECT IdServicio FROM catalogo_servicios WHERE Concepto = %s AND PrecioUnitario = %s LIMIT 1", (serv.concepto, serv.precio_unitario))
            serv_db = cursor.fetchone()
            
            if serv_db:
                id_serv = serv_db['IdServicio']
            else:
                # SI NO EXISTE O LE CAMBIÓ EL PRECIO, LO GUARDAMOS OCULTO PARA MANTENER LA INTEGRIDAD (EstadoActivo = 0)
                cursor.execute(
                    "INSERT INTO catalogo_servicios (Concepto, PrecioUnitario, TipoServicio, EstadoActivo) VALUES (%s, %s, %s, %s)",
                    (serv.concepto, serv.precio_unitario, 'Servicio Libre', 0)
                )
                id_serv = cursor.lastrowid
                
            detalles_a_guardar.append((folio_generado, id_serv, serv.cantidad, importe))

        iva = subtotal * 0.16
        gran_total = subtotal + iva

        # CLIENTES CIVILES U OCASIONALES (EstadoActivo = 0)
        id_cliente_final = peticion.cliente.id_cliente
        if id_cliente_final == 0:
            cursor.execute(
                "INSERT INTO clientes (RazonSocial, RFC, Contacto, Telefono, Domicilio, EstadoActivo) VALUES (%s, %s, %s, %s, %s, %s)",
                (peticion.cliente.nombre, 'XAXX010101000', peticion.cliente.atencion, '', '', 0)
            )
            id_cliente_final = cursor.lastrowid

        # INSERTAR CABECERA
        consulta_insert = """
            INSERT INTO cotizaciones (FolioCotizacion, IdCliente, FechaEmision, Subtotal, IVA, GranTotal) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores_insert = (folio_generado, id_cliente_final, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subtotal, iva, gran_total)
        cursor.execute(consulta_insert, valores_insert)

        # INSERTAR DETALLES PARA EL HISTORIAL Y LOS TRIGGERS
        if detalles_a_guardar:
            cursor.execute("SHOW COLUMNS FROM detalles_cotizacion")
            columnas_detalle = {col["Field"] for col in cursor.fetchall()}

            tiene_importe_camel = "ImporteLinea" in columnas_detalle
            tiene_importe_snake = "importe_linea" in columnas_detalle

            if not (tiene_importe_camel or tiene_importe_snake):
                raise HTTPException(status_code=500, detail="La tabla detalles_cotizacion no tiene columna de importe reconocida")

            if tiene_importe_camel and tiene_importe_snake:
                sql_detalle = (
                    "INSERT INTO detalles_cotizacion "
                    "(FolioCotizacion, IdServicio, Cantidad, ImporteLinea, importe_linea) "
                    "VALUES (%s, %s, %s, %s, %s)"
                )
                valores = [
                    (folio, id_serv, cantidad, importe, importe)
                    for (folio, id_serv, cantidad, importe) in detalles_a_guardar
                ]
            elif tiene_importe_snake:
                sql_detalle = (
                    "INSERT INTO detalles_cotizacion "
                    "(FolioCotizacion, IdServicio, Cantidad, importe_linea) "
                    "VALUES (%s, %s, %s, %s)"
                )
                valores = detalles_a_guardar
            else:
                sql_detalle = (
                    "INSERT INTO detalles_cotizacion "
                    "(FolioCotizacion, IdServicio, Cantidad, ImporteLinea) "
                    "VALUES (%s, %s, %s, %s)"
                )
                valores = detalles_a_guardar

            cursor.executemany(sql_detalle, valores)

        conexion.commit()

        # PREPARAR DATA PARA EL PDF FINAL
        resultado = {
            "folio": folio_generado,
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "cliente": { "nombre": peticion.cliente.nombre, "atencion": peticion.cliente.atencion },
            "conceptos_pdf": conceptos_pdf,
            "finanzas": { "subtotal": subtotal, "iva": iva, "gran_total": gran_total }
        }
        ruta_pdf = crear_pdf_cotizacion(resultado)

        return { "mensaje": "Cotización exitosa", "folio": folio_generado, "pdf_path": ruta_pdf }
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/api/v1/cotizaciones/historial")
async def obtener_historial_cotizaciones(request: Request, usuario: dict = Depends(obtener_usuario_actual)):
    conexion = obtener_conexion()
    if not conexion: raise HTTPException(status_code=500, detail="Error de BD")
    try:
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT c.FolioCotizacion AS folio, c.FechaEmision AS fecha_hora, cli.RazonSocial AS cliente
            FROM cotizaciones c LEFT JOIN clientes cli ON c.IdCliente = cli.IdCliente
            ORDER BY c.FechaEmision DESC LIMIT 50
        """
        cursor.execute(consulta)
        historial = cursor.fetchall()
        for item in historial:
            dt = item['fecha_hora']
            item['fecha'] = dt.strftime('%d/%m/%Y')
            item['hora'] = dt.strftime('%H:%M')
            item['url'] = construir_url_pdf(item['folio'], request)

        return {"historial": historial}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()