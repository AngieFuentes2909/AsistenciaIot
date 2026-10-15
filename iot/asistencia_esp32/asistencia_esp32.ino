// ============================================================
//  SISTEMA DE ASISTENCIA IOT COMPLETO
//  ESP32 + RFID RC522 + Teclado 4x4 + LCD 16x2 + Buzzer + WiFi + API
// ============================================================

#define BLYNK_TEMPLATE_ID "TMPL2og1sa6Ek"
#define BLYNK_TEMPLATE_NAME "Control de Asistencia IoT"
#define BLYNK_AUTH_TOKEN "-8ChkPCYpa0re-gcEiM69azP-AKHJJoN"

// ============================================================
//  CONFIGURACIÓN DE HARDWARE Y TECLADO
//  ───────────────────────────────────────────────────────────
//  true  = Modo con Teclado 4x4 conectado (para el jueves)
//  false = Modo solo RFID (para probar hoy sin teclado físico)
// ============================================================
#define USAR_TECLADO false 

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#if USAR_TECLADO
#include <Keypad.h>
#endif

// ============================================================
//  CREDENCIALES WIFI Y SERVIDOR
// ============================================================
// ⚠️ Coloca aquí el nombre y contraseña de tu red WiFi:
const char* WIFI_SSID     = "MOVISTAR_FIBRA_PLUS_CEC0";
const char* WIFI_PASSWORD = "zhpoeoS5UrSKsQwph5rb";

// 🌐 URL del Servidor en la Nube (Render):
const char* API_URL = "https://asistenciaiot.onrender.com/api/asistencias/registrar";

// ============================================================
//  PINES
// ============================================================
// RFID RC522 (SPI)
#define SS_PIN   5
#define RST_PIN  4
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Pin Buzzer
#define BUZZER_PIN 27

// Pantalla LCD I2C
LiquidCrystal_I2C lcd(0x27, 16, 2);

#if USAR_TECLADO
// Teclado Matricial 4x4
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {13, 14, 26, 16}; // Filas
byte colPins[COLS] = {17, 32, 33, 25}; // Columnas
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
String bufferTeclado = "";
#endif

String modoActual = "AUTO"; // "AUTO" alterna automáticamente entre Entrada y Salida

// Declaraciones
void beepExito();
void beepError();
void beepTecla();
void mostrarMensajeLCD(String linea1, String linea2);
void enviarAsistenciaAPI(String metodo, String identificador, String tipo);

void setup() {
  Serial.begin(115200);

  // Inicializar Buzzer
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // Inicializar LCD
  lcd.init();
  lcd.backlight();
  mostrarMensajeLCD("Iniciando...", "Conectando WiFi");

  // 1. Inicializar SPI y RFID RC522
  SPI.begin();
  mfrc522.PCD_Init();

  // Iniciar WiFi (Modo Estación)
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando a WiFi (" + String(WIFI_SSID) + ")");
  mostrarMensajeLCD("Conectando WiFi", String(WIFI_SSID).substring(0, 16));

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 30) {
    delay(500);
    Serial.print(".");
    intentos++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado! IP del ESP32: " + WiFi.localIP().toString());
    mostrarMensajeLCD("WiFi Conectado", WiFi.localIP().toString());
  } else {
    Serial.print("\nNo se pudo conectar. Codigo de estado: ");
    Serial.println(WiFi.status());
    if (WiFi.status() == 1) { // WL_NO_SSID_AVAIL
      Serial.println(">> AVISO: Red no encontrada. El ESP32 solo detecta WiFi 2.4GHz (no 5GHz/PLUS).");
    }
    mostrarMensajeLCD("Sin WiFi", "Revisa 2.4GHz");
  }
  delay(1500);

  mostrarMensajeLCD("Pase su tarjeta", "Bienvenido!");
  Serial.println(">> Lector RFID listo para escanear <<");
}

void loop() {
#if USAR_TECLADO
  // 1. REVISAR SI SE DIGITÓ EN EL TECLADO
  char key = keypad.getKey();
  if (key) {
    beepTecla();
    Serial.println("Tecla: " + String(key));

    if (key == 'A') {
      modoActual = "ENTRADA";
      mostrarMensajeLCD("Modo: ENTRADA", bufferTeclado == "" ? "Listo" : bufferTeclado);
    }
    else if (key == 'B') {
      modoActual = "SALIDA";
      mostrarMensajeLCD("Modo: SALIDA", bufferTeclado == "" ? "Listo" : bufferTeclado);
    }
    else if (key == '*') {
      bufferTeclado = "";
      mostrarMensajeLCD("Modo: " + modoActual, "Borrado");
      delay(800);
      mostrarMensajeLCD("Modo: " + modoActual, "Tarjeta o Codigo");
    }
    else if (key == '#') {
      if (bufferTeclado.length() > 0) {
        Serial.println("Enviando codigo: " + bufferTeclado);
        enviarAsistenciaAPI("TECLADO", bufferTeclado, modoActual);
        bufferTeclado = "";
      }
    }
    else {
      if (bufferTeclado.length() < 10) {
        bufferTeclado += key;
        mostrarMensajeLCD("Cod: " + bufferTeclado, "#:OK  *:Borrar");
      }
    }
  }
#endif

  // 2. REVISAR SI HAY TARJETA RFID CERCA (Verificación robusta)
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial())   return;

  String uidLeido = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uidLeido += "0";
    uidLeido += String(mfrc522.uid.uidByte[i], HEX);
  }
  uidLeido.toUpperCase();

  Serial.println("RFID detectado: " + uidLeido);
  enviarAsistenciaAPI("RFID", uidLeido, modoActual);

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}

// ============================================================
//  COMUNICACIÓN HTTP CON FASTAPI (Sin librerías adicionales)
// ============================================================
void enviarAsistenciaAPI(String metodo, String identificador, String tipo) {
  mostrarMensajeLCD("Enviando...", metodo);

  if (WiFi.status() != WL_CONNECTED) {
    beepError();
    mostrarMensajeLCD("Error de Red", "Sin conexion");
    delay(2000);
    mostrarMensajeLCD("Pase su tarjeta", "Bienvenido!");
    return;
  }

  WiFiClientSecure client;
  client.setInsecure(); // Conexión HTTPS sin requerir certificado raíz estático

  HTTPClient http;
  http.begin(client, API_URL);
  http.setTimeout(10000); // 10s para asegurar conexión estable en la nube
  http.addHeader("Content-Type", "application/json");

  // Armar JSON en formato de texto
  String jsonString = "{\"metodo\":\"" + metodo + "\",\"identificador\":\"" + identificador + "\",\"tipo\":\"" + tipo + "\",\"dispositivo_id\":\"ESP32_PORTAL_1\"}";

  int httpResponseCode = http.POST(jsonString);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Respuesta API (" + String(httpResponseCode) + "): " + response);

    // Comprobar si el acceso fue concedido
    bool acceso = (response.indexOf("\"acceso\":true") >= 0 || response.indexOf("\"acceso\": true") >= 0);

    // Extraer los mensajes personalizados para la pantalla LCD devueltos por la API
    String linea1 = "Acceso OK";
    String linea2 = "Bienvenid@!";

    int idx1 = response.indexOf("\"mensaje_lcd1\":");
    if (idx1 >= 0) {
      int p1 = response.indexOf("\"", idx1 + 15);
      int p2 = response.indexOf("\"", p1 + 1);
      if (p1 >= 0 && p2 > p1) {
        linea1 = response.substring(p1 + 1, p2);
      }
    }

    int idx2 = response.indexOf("\"mensaje_lcd2\":");
    if (idx2 >= 0) {
      int p1 = response.indexOf("\"", idx2 + 15);
      int p2 = response.indexOf("\"", p1 + 1);
      if (p1 >= 0 && p2 > p1) {
        linea2 = response.substring(p1 + 1, p2);
      }
    }

    if (acceso) {
      beepExito();
      mostrarMensajeLCD(linea1, linea2);
    } else {
      beepError();
      mostrarMensajeLCD("Acceso Denegado", "No registrado");
    }
  } else {
    beepError();
    Serial.println("Error HTTP: " + String(httpResponseCode));
    mostrarMensajeLCD("Error Servidor", "Codigo: " + String(httpResponseCode));
  }

  http.end();
  delay(2000);
  mostrarMensajeLCD("Pase su tarjeta", "Bienvenido!");
  Serial.println(">> Listo para la siguiente lectura <<");
}

// ============================================================
//  SEÑALES SONORAS Y LCD
// ============================================================
void beepTecla() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(30);
  digitalWrite(BUZZER_PIN, LOW);
}

void beepExito() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZER_PIN, LOW);
}

void beepError() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(150);
    digitalWrite(BUZZER_PIN, LOW);
    delay(100);
  }
}

void mostrarMensajeLCD(String linea1, String linea2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(linea1);
  lcd.setCursor(0, 1);
  lcd.print(linea2);
}
