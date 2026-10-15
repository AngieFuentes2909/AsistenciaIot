from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()

@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario_in: UsuarioCreate, db: Session = Depends(get_db)):
    # Validar documento duplicado
    existente = db.query(Usuario).filter(Usuario.documento == usuario_in.documento).first()
    if existente:
        raise HTTPException(status_code=400, detail="El documento ya se encuentra registrado.")

    # Validar rfid_uid duplicado si se proporciona
    if usuario_in.rfid_uid:
        usuario_in.rfid_uid = usuario_in.rfid_uid.strip().upper()
        existente_rfid = db.query(Usuario).filter(Usuario.rfid_uid == usuario_in.rfid_uid).first()
        if existente_rfid:
            raise HTTPException(status_code=400, detail="El UID RFID ya está asignado a otro usuario.")

    nuevo_usuario = Usuario(
        documento=usuario_in.documento.strip(),
        nombre=usuario_in.nombre.strip(),
        rfid_uid=usuario_in.rfid_uid,
        pin=usuario_in.pin.strip() if usuario_in.pin else None,
        departamento=usuario_in.departamento,
        activo=usuario_in.activo
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
