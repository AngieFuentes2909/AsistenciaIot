# Guía de Configuración: Blynk IoT Cloud

## 1. Crear Cuenta y Entrar a Blynk
1. Ve a [blynk.cloud](https://blynk.cloud) en tu navegador e inicia sesión (o crea una cuenta gratuita si aún no la tienes).
2. Si prefieres ver los datos en tu celular, descarga la app **Blynk IoT** desde Google Play o App Store e inicia sesión con la misma cuenta.

---

## 2. Crear el Template (Plantilla)
1. En el menú de la izquierda en la web de Blynk, haz clic en **Developer Zone** (icono de llave inglesa 🔧 o **Templates**).
2. Haz clic en el botón azul **"+ New Template"**.
3. Rellena los datos:
   - **Name**: `Control de Asistencia IoT`
   - **Hardware**: `ESP32`
   - **Connection Type**: `WiFi`
   - **Description**: Sistema de registro por RFID y Teclado.
4. Haz clic en **Done**.

---

## 3. Crear los Datastreams (Pines Virtuales)
Dentro de tu nueva plantilla, haz clic en la pestaña **Datastreams**:
Haz clic en **"+ New Datastream"** > **"Virtual Pin"** para cada uno de los siguientes:

### Pin V1: Nombre del Usuario
- **Name**: `Último Usuario`
- **Pin**: `V1`
- **Data Type**: `String`
- Haz clic en **Create**.

### Pin V2: Tipo de Registro
- **Name**: `Tipo Evento`
- **Pin**: `V2`
- **Data Type**: `String`
- Haz clic en **Create**.

### Pin V3: Método
- **Name**: `Método Utilizado`
- **Pin**: `V3`
- **Data Type**: `String`
- Haz clic en **Create**.

### Pin V4: Hora de Registro
- **Name**: `Hora Registro`
- **Pin**: `V4`
- **Data Type**: `String`
- Haz clic en **Create**.

> Haz clic en el botón verde **"Save"** (arriba a la derecha) para guardar los Datastreams.

---

## 4. Diseñar el Dashboard Web
1. En la misma plantilla, haz clic en la pestaña **Web Dashboard**.
2. Desde el panel izquierdo de widgets, arrastra los siguientes al centro:
   - **Value Display** (Widget 1):
     - Haz clic en el engranaje ⚙️ del widget.
     - Título: `Última Persona`.
     - Datastream: `V1 (Último Usuario)`.
     - Clic en **Save**.
   - **Value Display** (Widget 2):
     - Título: `Evento`.
     - Datastream: `V2 (Tipo Evento)`.
     - Clic en **Save**.
   - **Value Display** (Widget 3):
     - Título: `Método`.
     - Datastream: `V3 (Método Utilizado)`.
     - Clic en **Save**.
   - **Value Display** (Widget 4):
     - Título: `Hora`.
     - Datastream: `V4 (Hora Registro)`.
     - Clic en **Save**.
3. Haz clic en el botón verde **"Save and Apply"** (arriba a la derecha).

---

## 5. Crear el Dispositivo y Obtener el Token
1. En el menú lateral izquierdo de Blynk, ve a la sección de **Devices** (icono de lupa o 🖥️ **Devices**).
2. Haz clic en **"+ New Device"** > **"From template"**.
3. Selecciona:
   - **Template**: `Control de Asistencia IoT`.
   - **Device Name**: `ESP32 Lector`.
4. Haz clic en **Create**.
5. Verás en pantalla una ventana con tu **Auth Token** (o en la pestaña **Device Info** a la derecha):
   - Copia la línea que dice `BLYNK_AUTH_TOKEN = "..."` (o solo la cadena de letras/números del token).

---

## 6. Pegar el Token en el Backend
Abre el archivo `backend/.env` y pega tu token en la línea 4:
```env
BLYNK_AUTH_TOKEN=pega_aqui_tu_token_de_blynk
```
¡Y listo! Cada vez que se registre una tarjeta o un código de teclado, la API actualizará Blynk en tiempo real automáticamente.
