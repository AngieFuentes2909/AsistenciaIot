from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    documento = Column(String(50), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    rfid_uid = Column(String(50), unique=True, index=True, nullable=True)
    pin = Column(String(10), nullable=True)
    departamento = Column(String(100), default="General")
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    asistencias = relationship("Asistencia", back_populates="usuario")

class Asistencia(Base):
    __tablename__ = "asistencias"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), primary_key=True, server_default=func.now(), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    metodo = Column(String(20), nullable=False)  # 'RFID' o 'TECLADO'
    tipo = Column(String(20), nullable=False)    # 'ENTRADA' o 'SALIDA'
    dispositivo_id = Column(String(50), default="ESP32_MAIN")

    usuario = relationship("Usuario", back_populates="asistencias")
