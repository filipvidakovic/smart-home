# smart-home

# IoT Smart House System

Kompletno IoT rešenje za monitoring ulaznih vrata sa senzorima, MQTT komunikacijom, InfluxDB skladištenjem i Grafana vizualizacijom.

## 📋 Sadržaj

- [Pregled Sistema](#pregled-sistema)
- [Potrebni Alati](#potrebni-alati)
- [Instalacija](#instalacija)
- [Pokretanje](#pokretanje)
- [Konfiguracija](#konfiguracija)
- [Senzori](#senzori)
- [Vizualizacija](#vizualizacija)
- [Troubleshooting](#troubleshooting)

## 🏗️ Pregled Sistema

Sistem se sastoji od:

- **Raspberry Pi Device (PI1)** - Simulator senzora koji šalje podatke
- **MQTT Broker** - Eclipse Mosquitto za messaging
- **Flask Server** - Prikuplja podatke sa MQTT i čuva u InfluxDB
- **InfluxDB** - Time-series baza podataka
- **Grafana** - Vizualizacija podataka u real-time

### Arhitektura

```
┌─────────────┐     MQTT      ┌──────────────┐
│   PI1       │ ────────────> │ MQTT Broker  │
│  (Sensors)  │               │  (port 1883) │
└─────────────┘               └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ Flask Server │
                              │  (port 5000) │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐     ┌──────────────┐
                              │  InfluxDB    │────>│   Grafana    │
                              │  (port 8086) │     │  (port 3000) │
                              └──────────────┘     └──────────────┘
```

## 🛠️ Potrebni Alati

### Obavezno:

- **Python 3.9+**
- **Docker** i **Docker Compose**
- **Git**

### Python biblioteke (instaliraju se automatski):

- paho-mqtt
- influxdb-client
- Flask

## 📦 Instalacija

### 1. Kloniranje projekta

```bash
git clone <repository-url>
cd smart-house
```

### 2. Kreiranje Python virtuelnog okruženja

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalacija Python zavisnosti

```bash
cd RPI1
pip install -r requirements.txt
```

### 4. Setup Docker servisa

**Windows:**

```bash
setup_mqtt.bat
```

**Linux/Mac:**

```bash
chmod +x setup_mqtt.sh
./setup_mqtt.sh
```

## 🚀 Pokretanje

### Korak 1: Pokreni Docker servise

```bash
# Iz root direktorijuma projekta
docker-compose up -d
```

Proveri da li su svi servisi pokrenuti:

```bash
docker ps
```

Trebalo bi da vidiš 4 kontejnera:

- `mqtt5` - MQTT Broker
- `influxdb-iot` - InfluxDB
- `grafana-iot` - Grafana
- `flask-iot-server` - Flask server

### Korak 2: Verifikuj sistem (opcionalno)

```bash
# Iz RPI1 direktorijuma
python verify_system.py
```

### Korak 3: Pokreni PI1 senzore

```bash
cd RPI1
python main.py
```

Trebalo bi da vidiš:

```
==================================================
Starting IoT Device Application
==================================================

Device Configuration:
  PI ID: PI1
  Device Name: RaspberryPi_Entrance
  Location: Building_A_Floor_1
  Description: Main entrance monitoring device

✓ MQTT Publisher ready
✓ DS1 Door Sensor started
✓ DPIR1 Motion Sensor started
✓ DUS1 Distance Sensor started
✓ DMS Console started
...

System running... Press Ctrl+C to stop
```

### Korak 4: Otvori Grafana Dashboard

1. Otvori browser: **http://localhost:3000**
2. Login: `admin` / `admin`
3. Idi na **Configuration** → **Data Sources** → **Add data source**
4. Izaberi **InfluxDB**
5. Popuni:

```
   Name: InfluxDB-IoT
   Query Language: Flux
   URL: http://influxdb:8086
   Organization: myorg
   Token: adminadmin
   Default Bucket: iot
```

6. Klikni **Save & Test**
7. Idi na **Dashboards** → **Import** → Copy/paste JSON iz `grafana/dashboards/iot-sensors.json`

## ⚙️ Konfiguracija

### Senzori (RPI1/settings/settings.json)

```json
{
  "device": {
    "pi_id": "PI1",
    "device_name": "RaspberryPi_Entrance",
    "location": "Building_A_Floor_1"
  },
  "mqtt": {
    "broker": "localhost",
    "port": 1883,
    "batch_size": 5,
    "batch_interval": 10
  },
  "DS1": {
    "simulated": true,
    "sensor_type": "door"
  },
  "DPIR1": {
    "simulated": true,
    "sensor_type": "motion"
  },
  "DUS1": {
    "simulated": true,
    "read_interval": 1,
    "sensor_type": "distance"
  }
}
```

### Promeni sa simuliranih na realne senzore

Promeni `"simulated": false` i dodaj GPIO pinove:

```json
{
  "DS1": {
    "pin": 4,
    "led_pin": 18,
    "simulated": false
  }
}
```

## 🔍 Senzori

| Senzor | Tip         | Meri                             | Topic              |
| ------ | ----------- | -------------------------------- | ------------------ |
| DS1    | Door Sensor | Otvaranje/zatvaranje vrata (0/1) | `sensors/door`     |
| DPIR1  | PIR Motion  | Detekcija pokreta (0/1)          | `sensors/motion`   |
| DUS1   | Ultrasonic  | Udaljenost u cm (10-200)         | `sensors/distance` |

## 📊 Vizualizacija

### Grafana Panels

1. **Temperature Panel** - Line chart temperaturu (ako dodaš DS18B20)
2. **Motion Panel** - State timeline za detekciju pokreta
3. **Distance Panel** - Line chart udaljenosti
4. **Door Panel** - State timeline otvaranja vrata

### Flux Query Primer

```flux
from(bucket: "iot")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "motion")
  |> filter(fn: (r) => r["_field"] == "value")
```

## 🔧 Troubleshooting

### Problem: MQTT Connection Refused

```bash
# Proveri da li MQTT radi
docker logs mqtt5

# Restartuj MQTT
docker-compose restart mqtt5
```

### Problem: Flask Server ne prima podatke

```bash
# Proveri Flask logove
docker logs -f flask-iot-server

# Proveri MQTT test
mosquitto_sub -h localhost -p 1883 -t "sensors/#" -v
```

### Problem: Grafana nema podataka

```bash
# Proveri da li ima podataka u InfluxDB
curl http://localhost:5000/stats

# Trebalo bi da vidiš:
# {"door": 10, "motion": 15, "distance": 20}
```

### Problem: Docker servisi ne rade

```bash
# Rebuild svih servisa
docker-compose down
docker-compose build
docker-compose up -d

# Proveri logove
docker-compose logs
```

## 📱 Korisne Komande

```bash
# Proveri status servisa
docker ps

# Prati logove
docker logs -f flask-iot-server
docker logs -f mqtt5

# Zaustavi sistem
docker-compose down

# Očisti sve (uključujući podatke)
docker-compose down -v

# Rebuild Flask servera
docker-compose build flask-server
docker-compose up -d flask-server

# Test MQTT publish
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "Hello MQTT"

# Test MQTT subscribe
mosquitto_sub -h localhost -p 1883 -t "sensors/#" -v
```

## 🌐 Web Interfejsi

- **Grafana**: http://localhost:3000 (admin/admin)
- **InfluxDB**: http://localhost:8086 (admin/adminadmin)
- **Flask Health**: http://localhost:5000/health
- **Flask Stats**: http://localhost:5000/stats

## 🎯 DMS Console Komande

Kada pokreneš `python main.py`, imaš pristup konzoli:

```
> dms 1234          # Unlock vrata (LED on 3s)
> db                # Doorbell (buzzer)
> led_on            # Upali LED
> led_off           # Ugasi LED
> exit              # Zatvori aplikaciju
```

## 📝 Struktura Projekta

```
smart-house/
├── RPI1/
│   ├── components/        # Sensor komponente
│   ├── sensors/          # Realni senzori
│   ├── simulators/       # Simulatori
│   ├── mqtt/            # MQTT publisher
│   ├── settings/        # Konfiguracija
│   └── main.py          # Glavna aplikacija
├── server/
│   ├── app.py           # Flask server
│   ├── Dockerfile
│   └── requirements.txt
├── grafana/
│   └── dashboards/      # Grafana JSON
├── config/              # MQTT config
├── docker-compose.yml
└── README.md
```

## 🤝 Kontribucija

Za pitanja ili probleme, otvori issue na GitHub-u.

## 📄 Licenca

MIT License
