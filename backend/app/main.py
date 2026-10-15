import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import asistencias, usuarios

app = FastAPI(
    title="API de Control de Asistencia IoT",
    description="Backend con FastAPI y TimescaleDB para lector RFID y Teclado Matricial ESP32.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asistencias.router)
app.include_router(usuarios.router)

# Montar interfaz web estática en http://localhost:8000/dashboard
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/dashboard", StaticFiles(directory=frontend_dir, html=True), name="dashboard")

@app.get("/")
def root():
    return {
        "sistema": "API Asistencia IoT",
        "estado": "Activo",
        "panel_web": "http://localhost:8000/dashboard",
        "docs": "http://localhost:8000/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}
