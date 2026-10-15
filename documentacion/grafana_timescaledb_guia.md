# Guía de Conexión y Consultas: Grafana + TimescaleDB

## 1. Conectar Grafana a TimescaleDB

1. Abre tu navegador en `http://localhost:3000` (Grafana).
2. Usuario y contraseña por defecto: `admin` / `admin`.
3. Ve a **Connections** > **Data Sources** > **Add data source**.
4. Selecciona **PostgreSQL**.
5. Configura los parámetros:
   - **Host URL**: `timescaledb:5432` (si Grafana corre en Docker en la misma red) o `host.docker.internal:5432` / `localhost:5432`.
   - **Database name**: `asistencia_db`
   - **User**: `postgres`
   - **Password**: `password123`
   - **TLS/SSL Mode**: `disable`
   - **TimescaleDB**: Activa la casilla `TimescaleDB` en la parte inferior.
6. Haz clic en **Save & Test**.

---

## 2. Consultas SQL listas para Grafana

### Panel 1: Flujo de Asistencias por Franja Horaria (Time Series)
> Muestra picos de entrada/salida a lo largo del día usando `time_bucket`.
```sql
SELECT
  time_bucket('30 minutes', timestamp) AS time,
  tipo,
  count(*) AS total
FROM asistencias
WHERE $__timeFilter(timestamp)
GROUP BY 1, 2
ORDER BY 1;
```

### Panel 2: Comparativa de Uso: RFID vs Teclado (Pie Chart / Bar Gauge)
```sql
SELECT
  metodo AS metric,
  count(*) AS cantidad
FROM asistencias
WHERE $__timeFilter(timestamp)
GROUP BY metodo;
```

### Panel 3: Contador de Asistencias del Día (Stat Panel)
```sql
SELECT
  count(*) AS "Total Hoy"
FROM asistencias
WHERE timestamp >= CURRENT_DATE;
```

### Panel 4: Registro Detallado en Tiempo Real (Table Panel)
```sql
SELECT
  a.timestamp AS "Hora",
  u.nombre AS "Persona",
  u.documento AS "Doc/Código",
  a.tipo AS "Evento",
  a.metodo AS "Vía",
  a.dispositivo_id AS "Punto de Acceso"
FROM asistencias a
JOIN usuarios u ON a.usuario_id = u.id
ORDER BY a.timestamp DESC
LIMIT 50;
```
