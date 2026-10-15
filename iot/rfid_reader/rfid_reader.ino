// ============================================================
//  APP ASISTENCIA - Lector RFID con LCD y Buzzer
//  Placa: ESP32-WROOM-32 DevKit
// ============================================================
//
//  DIAGRAMA DE CONEXIONES
//  ─────────────────────────────────────────────────────────
//  Módulo RFID RC522:
//    SDA (SS) → GPIO 5
//    SCK      → GPIO 18   (SPI bus por defecto del ESP32)
//    MOSI     → GPIO 23
//    MISO     → GPIO 19
//    RST      → GPIO 4
//    3.3V     → 3V3
//    GND      → GND
//
//  Pantalla LCD 16x2 con módulo I2C:
//    SDA      → GPIO 21
//    SCL      → GPIO 22
//    VCC      → 5V (VIN)
//    GND      → GND
//
//  Buzzer Activo:
//    (+)      → GPIO 27
//    (-)      → GND
// ============================================================

#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- Pines RFID RC522 ---
#define SS_PIN   5    // SDA (SS)
#define RST_PIN  4    // RST

// --- Pin Buzzer Activo ---
#define BUZZER_PIN  27

// --- Pantalla LCD I2C (16 columnas x 2 filas) ---
// Cambia 0x27 por 0x3F si la pantalla no enciende
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Instancia del lector RFID
MFRC522 mfrc522(SS_PIN, RST_PIN);

// ============================================================
//  BASE DE DATOS DE TARJETAS REGISTRADAS
//  → Pasa cada tarjeta por el lector, copia el UID que
//    aparece en el Monitor Serie y agrégalo aquí.
//  → El UID debe estar en MAYÚSCULAS (el código lo convierte
//    automáticamente).
// ============================================================
struct Usuario {
  String uid;
  String nombre;
};

Usuario usuarios[] = {
  {"04E8A232", "Angie Gomez"},
  {"A3B5C7D9", "Juan Perez"},
  {"F1E2D3C4", "Maria Lopez"}
};
const int numUsuarios = sizeof(usuarios) / sizeof(usuarios[0]);

// ============================================================
//  SETUP
// ============================================================
void setup() {
  Serial.begin(115200);

  // --- Iniciar SPI y lector RFID ---
  SPI.begin();
  mfrc522.PCD_Init();

  // --- Iniciar Buzzer ---
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // --- Iniciar LCD ---
  lcd.init();
  lcd.backlight();

  // --- Pantalla de inicio ---
  mostrarMensajeLCD("Coloca tu carnet", "Bienvenido!");

  Serial.println(F("===================================="));
  Serial.println(F("  Sistema de Asistencia RFID listo  "));
  Serial.println(F("===================================="));
  Serial.println(F("Esperando tarjeta..."));
}

// ============================================================
//  LOOP PRINCIPAL
// ============================================================
void loop() {
  // Esperar a que haya una tarjeta nueva cerca
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial())   return;

  // --- Leer UID y convertirlo a texto en MAYÚSCULAS ---
  String uidLeido = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uidLeido += "0";
    uidLeido += String(mfrc522.uid.uidByte[i], HEX);
  }
  uidLeido.toUpperCase();

  Serial.print(F("Tarjeta detectada - UID: "));
  Serial.println(uidLeido);

  // --- Buscar si la tarjeta está registrada ---
  String nombrePersona = "";
  for (int i = 0; i < numUsuarios; i++) {
    if (usuarios[i].uid == uidLeido) {
      nombrePersona = usuarios[i].nombre;
      break;
    }
  }

  // --- Respuesta según resultado ---
  if (nombrePersona != "") {
    // ✅ Tarjeta registrada → 1 beep corto + mensaje amigable
    beepExito();
    mostrarMensajeLCD("Hola de nuevo!", nombrePersona);
    Serial.println("Asistencia registrada: " + nombrePersona + " (" + uidLeido + ")");
  } else {
    // ❌ Tarjeta desconocida → 2 beeps + aviso
    beepError();
    mostrarMensajeLCD("Tarjeta no valida", "Intenta de nuevo");
    Serial.println(F("Tarjeta NO registrada."));
  }

  // Pausa para que el usuario lea el mensaje
  delay(3000);

  // Volver a la pantalla de inicio
  mostrarMensajeLCD("Coloca tu carnet", "Bienvenido!");

  // Detener comunicación con la tarjeta actual
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}

// ============================================================
//  FUNCIONES AUXILIARES
// ============================================================

// 1 beep corto (tarjeta registrada)
void beepExito() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZER_PIN, LOW);
}

// 2 beeps (tarjeta no registrada)
void beepError() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(150);
  digitalWrite(BUZZER_PIN, LOW);
  delay(120);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(150);
  digitalWrite(BUZZER_PIN, LOW);
}

// Mostrar dos líneas en el LCD
void mostrarMensajeLCD(String linea1, String linea2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(linea1);
  lcd.setCursor(0, 1);
  lcd.print(linea2);
}
