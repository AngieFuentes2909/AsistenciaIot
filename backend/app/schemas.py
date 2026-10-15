from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- Esquemas de Usuario ---
class UsuarioBase(BaseModel):
    documento: str
    nombre: str
    rfid_uid: Optional[str] = None
    pin: Optional[str] = None
    departamento: Optional[str] = "General"
    cargo: Optional[str] = "Docente"
    activo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioResponse(UsuarioBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Esquemas de Asistencia ---
class RegistroAsistenciaRequest(BaseModel):
    metodo: str           # "RFID" o "TECLADO"
    identificador: str    # UID de tarjeta si es RFID, o Documento/Código si es TECLADO
    pin: Optional[str] = None
    tipo: Optional[str] = "ENTRADA"  # "ENTRADA" o "SALIDA"
    dispositivo_id: Optional[str] = "ESP32_MAIN"

class RegistroAsistenciaResponse(BaseModel):
    acceso: bool
    mensaje: str
    usuario_nombre: Optional[str] = None
    metodo: str
    tipo: str
    timestamp: datetime
    mensaje_lcd1: Optional[str] = None
    mensaje_lcd2: Optional[str] = None

class AsistenciaItemResponse(BaseModel):
    id: int
    timestamp: datetime
    usuario_id: int
    usuario_nombre: str
    metodo: str
    tipo: str
    dispositivo_id: str

    class Config:
        from_attributes = True
