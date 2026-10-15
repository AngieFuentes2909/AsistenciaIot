import logging
import httpx
from app.config import settings

from datetime import datetime

logger = logging.getLogger(__name__)

async def actualizar_blynk(usuario_nombre: str, tipo: str, metodo: str, hora_str: str = None):
    """
    Actualiza pines virtuales en Blynk Cloud vía REST API si BLYNK_AUTH_TOKEN está configurado.
    Pines:
      V1: Último usuario registrado (String)
      V2: Tipo de registro (ENTRADA / SALIDA)
      V3: Método utilizado (RFID / TECLADO)
      V4: Hora del registro (HH:MM:SS)
    """
    token = settings.BLYNK_AUTH_TOKEN
    if not token:
        logger.info("[Blynk] No hay BLYNK_AUTH_TOKEN configurado, omitiendo actualización a Blynk.")
        return

    if not hora_str:
        hora_str = datetime.now().strftime("%I:%M:%S %p")

    try:
        url = f"{settings.BLYNK_SERVER_URL}/batch/update"
        params = {
            "token": token,
            "v1": usuario_nombre,
            "v2": tipo,
            "v3": metodo,
            "v4": hora_str
        }
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                logger.info(f"[Blynk] Actualizado exitosamente: {usuario_nombre} ({tipo})")
            else:
                logger.warning(f"[Blynk] Respuesta de Blynk: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"[Blynk] Error al actualizar estado en Blynk: {e}")
