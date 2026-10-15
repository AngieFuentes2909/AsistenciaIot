from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Optional

from app.database import get_db
from app.models import Usuario, Asistencia
from app.schemas import RegistroAsistenciaRequest, RegistroAsistenciaResponse, AsistenciaItemResponse
from app.services.blynk_service import actualizar_blynk

router = APIRouter(prefix="/api/asistencias", tags=["Asistencias"])

@router.post("/registrar", response_model=RegistroAsistenciaResponse)
async def registrar_asistencia(
    data: RegistroAsistenciaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    metodo = data.metodo.strip().upper()
    identificador = data.identificador.strip().upper()
    tipo = (data.tipo or "ENTRADA").strip().upper()
    dispositivo = data.dispositivo_id or "ESP32_MAIN"

    usuario = None

    if metodo == "RFID":
        usuario = db.query(Usuario).filter(
            Usuario.rfid_uid == identificador,
            Usuario.activo == True
        ).first()
    elif metodo == "TECLADO":
        # Búsqueda por documento o código digitado
        usuario = db.query(Usuario).filter(
            Usuario.documento == identificador,
            Usuario.activo == True
        ).first()

        # Si el usuario tiene un PIN configurado, validarlo si fue enviado
        if usuario and usuario.pin:
            if data.pin and data.pin != usuario.pin:
                return RegistroAsistenciaResponse(
                    acceso=False,
                    mensaje="PIN incorrecto",
                    usuario_nombre=None,
                    metodo=metodo,
                    tipo=tipo,
                    timestamp=datetime.now(timezone.utc)
                )
    else:
        raise HTTPException(status_code=400, detail="Método no soportado. Use 'RFID' o 'TECLADO'.")

    if not usuario:
        return RegistroAsistenciaResponse(
            acceso=False,
            mensaje="Usuario o tarjeta no registrada",
            usuario_nombre=None,
            metodo=metodo,
            tipo=tipo,
            timestamp=datetime.now(timezone.utc)
        )

    # --- Alternancia Inteligente de Entrada / Salida ---
    ultimo_registro = (
        db.query(Asistencia)
        .filter(Asistencia.usuario_id == usuario.id)
        .order_by(Asistencia.timestamp.desc())
        .first()
    )

    tipo_solicitado = (data.tipo or "AUTO").strip().upper()
    if tipo_solicitado in ["ENTRADA", "SALIDA"]:
        tipo = tipo_solicitado
    else:
        # Modo AUTO: si no tiene registro o el último fue SALIDA -> ENTRADA
        # Si el último fue ENTRADA -> SALIDA
        if not ultimo_registro or ultimo_registro.tipo == "SALIDA":
            tipo = "ENTRADA"
        else:
            tipo = "SALIDA"

    # Preparar mensajes para la pantalla LCD del colegio
    nombre_limpio = usuario.nombre.replace("Lic. ", "").replace("Prof. ", "").strip()
    primer_nombre = nombre_limpio.split()[0]
    if tipo == "ENTRADA":
        lcd1 = f"Prof. {primer_nombre}"[:16]
        lcd2 = "Bienvenid@!"
    else:
        lcd1 = "Hasta luego!"
        lcd2 = f"Prof. {primer_nombre}"[:16]

    # Crear el registro de asistencia en la base de datos (TimescaleDB hypertable)
    ahora = datetime.now(timezone.utc)
    nueva_asistencia = Asistencia(
        timestamp=ahora,
        usuario_id=usuario.id,
        metodo=metodo,
        tipo=tipo,
        dispositivo_id=dispositivo
    )
    db.add(nueva_asistencia)
    db.commit()
    db.refresh(nueva_asistencia)

    # Actualizar Blynk en segundo plano
    background_tasks.add_task(actualizar_blynk, usuario.nombre, tipo, metodo)

    return RegistroAsistenciaResponse(
        acceso=True,
        mensaje=f"Acceso concedido ({tipo.lower()})",
        usuario_nombre=usuario.nombre,
        metodo=metodo,
        tipo=tipo,
        timestamp=ahora,
        mensaje_lcd1=lcd1,
        mensaje_lcd2=lcd2
    )

@router.get("/recientes", response_model=List[AsistenciaItemResponse])
def listar_asistencias_recientes(limit: int = 20, db: Session = Depends(get_db)):
    registros = (
        db.query(Asistencia)
        .order_by(Asistencia.timestamp.desc())
        .limit(limit)
        .all()
    )

    resultado = []
    for reg in registros:
        resultado.append(AsistenciaItemResponse(
            id=reg.id,
            timestamp=reg.timestamp,
            usuario_id=reg.usuario_id,
            usuario_nombre=reg.usuario.nombre if reg.usuario else "Desconocido",
            metodo=reg.metodo,
            tipo=reg.tipo,
            dispositivo_id=reg.dispositivo_id
        ))
    return resultado

@router.get("/resumen")
def obtener_resumen(db: Session = Depends(get_db)):
    hoy = datetime.now(timezone.utc).date()
    total_hoy = db.query(Asistencia).filter(func.date(Asistencia.timestamp) == hoy).count()
    entradas_hoy = db.query(Asistencia).filter(func.date(Asistencia.timestamp) == hoy, Asistencia.tipo == "ENTRADA").count()
    salidas_hoy = db.query(Asistencia).filter(func.date(Asistencia.timestamp) == hoy, Asistencia.tipo == "SALIDA").count()
    rfid_count = db.query(Asistencia).filter(func.date(Asistencia.timestamp) == hoy, Asistencia.metodo == "RFID").count()
    teclado_count = db.query(Asistencia).filter(func.date(Asistencia.timestamp) == hoy, Asistencia.metodo == "TECLADO").count()

    return {
        "fecha": str(hoy),
        "total_registros_hoy": total_hoy,
        "entradas_hoy": entradas_hoy,
        "salidas_hoy": salidas_hoy,
        "por_metodo": {
            "RFID": rfid_count,
            "TECLADO": teclado_count
        }
    }

@router.get("/reporte")
def generar_reporte(
    fecha_inicio: Optional[str] = None, # Formato YYYY-MM-DD
    fecha_fin: Optional[str] = None,    # Formato YYYY-MM-DD
    tipo: Optional[str] = None,         # "ENTRADA", "SALIDA" o vacío para ambos
    metodo: Optional[str] = None,       # "RFID", "TECLADO" o vacío para ambos
    area: Optional[str] = None,         # Área o Asignatura (Español, Educación Física, etc.)
    usuario_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint de reportería avanzada para el Rector / Gerente.
    Permite filtrar por rangos de fecha (diario, semanal, mensual o personalizado),
    tipo de marcación, método y área/materia del docente.
    """
    query = db.query(Asistencia).join(Usuario)

    if fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            query = query.filter(Asistencia.timestamp >= dt_inicio)
        except ValueError:
            pass

    if fecha_fin:
        try:
            dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(Asistencia.timestamp <= dt_fin)
        except ValueError:
            pass

    if tipo and tipo.strip().upper() in ["ENTRADA", "SALIDA"]:
        query = query.filter(Asistencia.tipo == tipo.strip().upper())

    if metodo and metodo.strip().upper() in ["RFID", "TECLADO"]:
        query = query.filter(Asistencia.metodo == metodo.strip().upper())

    if area and area.strip() and area.strip().upper() != "TODAS":
        query = query.filter(Usuario.departamento.ilike(f"%{area.strip()}%"))

    if usuario_id:
        query = query.filter(Asistencia.usuario_id == usuario_id)

    registros = query.order_by(Asistencia.timestamp.desc()).all()

    resultado = []
    for reg in registros:
        docente = reg.usuario
        resultado.append({
            "id": reg.id,
            "timestamp": reg.timestamp.isoformat(),
            "fecha": reg.timestamp.strftime("%Y-%m-%d"),
            "hora": reg.timestamp.strftime("%H:%M:%S"),
            "docente_id": reg.usuario_id,
            "docente_nombre": docente.nombre if docente else "Desconocido",
            "documento": docente.documento if docente else "",
            "area": docente.departamento if docente else "General",
            "cargo": getattr(docente, "cargo", "Docente") or "Docente",
            "tipo": reg.tipo,
            "metodo": reg.metodo,
            "dispositivo_id": reg.dispositivo_id
        })

    return resultado

