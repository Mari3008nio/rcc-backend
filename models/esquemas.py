from pydantic import BaseModel
from typing import List

class RenglonServicio(BaseModel):
    concepto: str
    precio_unitario: float
    cantidad: float

# Molde completo para el cliente nuevo o existente
class ClienteCotizacion(BaseModel):
    nombre: str
    domicilio: str
    ciudad: str
    rfc: str

class PeticionCotizacion(BaseModel):
    cliente: ClienteCotizacion 
    servicios: List[RenglonServicio]
    # --- AGREGAR AL FINAL DE esquemas.py ---

class ClienteBase(BaseModel):
    razon_social: str
    rfc: str
    contacto: str # Aquí guardaremos domicilio, ciudad y teléfono juntos

class ClienteRespuesta(ClienteBase):
    id_cliente: int