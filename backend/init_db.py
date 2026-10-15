import time
from sqlalchemy import text
from app.database import engine, Base, SessionLocal
from app.models import Usuario

def inicializar_base_de_datos():
    print("Conectando a PostgreSQL y aplicando extensiones...")
    with engine.connect() as conn:
        # Activar extensión TimescaleDB
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            conn.commit()
            print("Extension TimescaleDB verificada/activada.")
        except Exception as e:
            print(f"Nota sobre TimescaleDB: {e}")

    # Crear tablas
    print("Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)

    # Convertir asistencias en Hypertable de TimescaleDB
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT create_hypertable('asistencias', 'timestamp', if_not_exists => TRUE);"))
            conn.commit()
            print("Hypertable 'asistencias' creada o verificada en TimescaleDB.")
        except Exception as e:
            print(f"Aviso al crear hypertable (podría ya existir o estar en modo postgres): {e}")

    # Sembrar usuarios de prueba iniciales
    db = SessionLocal()
    try:
        usuarios_iniciales = [
            {
                "documento": "1001",
                "nombre": "Angie Gomez",
                "rfid_uid": "86557F05",
                "pin": "1234",
                "departamento": "Ingeniería"
            },
            {
                "documento": "1002",
                "nombre": "Juan Perez",
                "rfid_uid": "EABB8005",
                "pin": "5678",
                "departamento": "Recursos Humanos"
            },
            {
                "documento": "1003",
                "nombre": "Maria Lopez",
                "rfid_uid": "F1E2D3C4",
                "pin": "0000",
                "departamento": "Finanzas"
            }
        ]

        for u_data in usuarios_iniciales:
            existe = db.query(Usuario).filter(Usuario.documento == u_data["documento"]).first()
            if not existe:
                nuevo = Usuario(**u_data)
                db.add(nuevo)
                print(f"Usuario creado: {u_data['nombre']} (Doc: {u_data['documento']} | UID: {u_data['rfid_uid']} | PIN: {u_data['pin']})")
        db.commit()
        print("Inicialización completada con éxito.")
    finally:
        db.close()

if __name__ == "__main__":
    inicializar_base_de_datos()
