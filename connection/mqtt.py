import paho.mqtt.client as mqtt
import time
import random

# ─────────────────────────────────────────
#  KONFIGURASI BROKER
# ─────────────────────────────────────────
BROKER    = "127.0.0.1"
PORT      = 1883
CLIENT_ID = "python-aveva-gabungan"

# ─────────────────────────────────────────
#  TOPIC PUBLISH (Python → AVEVA)
#  Data sensor yang dikirim ke AVEVA Edge
# ─────────────────────────────────────────

# pump
TOPIC_PUMP_ACID = "sensor/pump_acid"
TOPIC_PUMP_SLURRY = "sensor/pump_slurry"

# PREHEATER 1
TOPIC_PREHEATER1_SUHU     = "sensor/preheater1/suhu"
TOPIC_PREHEATER1_TEKANAN  = "sensor/preheater1/tekanan"
TOPIC_PREHEATER1_STATUS    = "sensor/preheater1/status"
TOPIC_SLURRY_FLOWP_P1 = "sensor/preheater1/slurry_flowp1"

# PREHEATER 2
TOPIC_PREHEATER2_SUHU     = "sensor/preheater2/suhu"
TOPIC_PREHEATER2_TEKANAN  = "sensor/preheater2/tekanan"
TOPIC_PREHEATER2_STATUS    = "sensor/preheater2/status"
TOPIC_SLURRY_FLOWP_P2 = "sensor/preheater2/slurry_flowp2"

# REACTOR 1
TOPIC_REACTOR1_SUHU     = "sensor/reactor1/suhu"
TOPIC_REACTOR1_TEKANAN  = "sensor/reactor1/tekanan"
TOPIC_REACTOR1_STATUS    = "sensor/reactor1/status"
TOPIC_SLURRY_FLOWP_B1 = "sensor/reactor1/slurry_flowp1"

# REACTOR 2
TOPIC_REACTOR2_SUHU     = "sensor/reactor2/suhu"
TOPIC_REACTOR2_TEKANAN  = "sensor/reactor2/tekanan"
TOPIC_REACTOR2_STATUS    = "sensor/reactor2/status"
TOPIC_SLURRY_FLOWP_B2 = "sensor/reactor2/slurry_flowp2"

# VESSEL 1
TOPIC_VESSEL1_SUHU     = "sensor/vessel1/suhu"
TOPIC_VESSEL1_TEKANAN  = "sensor/vessel1/tekanan"
TOPIC_VESSEL1_STATUS    = "sensor/vessel1/status"
TOPIC_SLURRY_FLOWP_V1 = "sensor/vessel1/slurry_flowp1"

# VESSEL 2
TOPIC_VESSEL2_SUHU     = "sensor/vessel2/suhu"
TOPIC_VESSEL2_TEKANAN  = "sensor/vessel2/tekanan"
TOPIC_VESSEL2_STATUS    = "sensor/vessel2/status"
TOPIC_SLURRY_FLOWP_V2 = "sensor/vessel2/slurry_flowp2"

# ─────────────────────────────────────────
#  TOPIC SUBSCRIBE (AVEVA → Python)
#  Nilai yang dikirim dari dashboard AVEVA
# ─────────────────────────────────────────
TOPIC_SETPOINT_SUHU_PREHEATER1     = "output/setpoint_suhu_preheater1"
TOPIC_SETPOINT_SUHU_PREHEATER2     = "output/setpoint_suhu_preheater2"
TOPIC_SETPOINT_SUHU_REACTOR1        = "output/setpoint_suhu_reactor1"
TOPIC_SETPOINT_SUHU_REACTOR2        = "output/setpoint_suhu_reactor2"
TOPIC_SETPOINT_PUMP_ACID          = "output/setpoint_pump_acid"
TOPIC_SETPOINT_PUMP_SLURRY        = "output/setpoint_pump_slurry"


# ─────────────────────────────────────────
#  VARIABEL GLOBAL SETPOINT
# ─────────────────────────────────────────
setpoint_suhu_preheater1 = None
setpoint_suhu_preheater2 = None
setpoint_suhu_reactor1 = None
setpoint_suhu_reactor2 = None
setpoint_pump_acid = None
setpoint_pump_slurry = None


class MQTTClient:
    def __init__(self, broker, port, client_id):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def send_message(self, topic, payload):
        try:
            self.client.publish(topic, payload, qos=1)
            print(f"  [Kirim] -> {topic}: {payload}")
        except Exception as e:
            print(f"[Error] Gagal mengirim pesan: {e}")

    def connect(self):
        print(f"Menghubungkan ke broker {self.broker}:{self.port} ...")
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            time.sleep(1)
        except Exception as e:
            print(f"[Error] Tidak bisa terhubung ke broker: {e}")
            print("Pastikan Mosquitto sudah berjalan di port 1883")
            exit(1)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[OK] Terhubung ke MQTT Broker!")
            # Subscribe semua topic dari AVEVA
            client.subscribe(TOPIC_SETPOINT_SUHU_PREHEATER1)
            client.subscribe(TOPIC_SETPOINT_SUHU_PREHEATER2)
            client.subscribe(TOPIC_SETPOINT_SUHU_REACTOR1)
            client.subscribe(TOPIC_SETPOINT_SUHU_REACTOR2)
            client.subscribe(TOPIC_SETPOINT_PUMP_ACID)
            client.subscribe(TOPIC_SETPOINT_PUMP_SLURRY)

            print("📡 Subscribe ke topic AVEVA berhasil")
            print("─" * 50)
        else:
            print(f"❌ Gagal terhubung, kode error: {rc}")

    def on_message(self, client, userdata, msg):
        global setpoint_suhu_preheater1, setpoint_suhu_preheater2
        global setpoint_suhu_reactor1, setpoint_suhu_reactor2
        global setpoint_pump_acid, setpoint_pump_slurry

        topic = msg.topic
        payload = msg.payload.decode()
        print(f"📥 Terima → {topic}: {payload}")

        if topic == TOPIC_SETPOINT_SUHU_PREHEATER1:
            setpoint_suhu_preheater1 = payload
        elif topic == TOPIC_SETPOINT_SUHU_PREHEATER2:
            setpoint_suhu_preheater2 = payload
        elif topic == TOPIC_SETPOINT_SUHU_REACTOR1:
            setpoint_suhu_reactor1 = payload
        elif topic == TOPIC_SETPOINT_SUHU_REACTOR2:
            setpoint_suhu_reactor2 = payload
        elif topic == TOPIC_SETPOINT_PUMP_ACID:
            setpoint_pump_acid = payload
        elif topic == TOPIC_SETPOINT_PUMP_SLURRY:
            setpoint_pump_slurry = payload


if __name__ == "__main__":
    mqtt_client = MQTTClient(BROKER, PORT, CLIENT_ID)
    mqtt_client.connect()
    client = mqtt_client.client

    try:
        while True:
            # Generate nilai simulasi sensor
            suhu_preheater1 = round(random.uniform(25.0, 85.0), 2)
            suhu_preheater2 = round(random.uniform(25.0, 85.0), 2)
            suhu_reactor1 = round(random.uniform(25.0, 85.0), 2)
            suhu_reactor2 = round(random.uniform(25.0, 85.0), 2)
            tekanan_preheater1 = round(random.uniform(1.0, 5.0), 2)
            tekanan_preheater2 = round(random.uniform(1.0, 5.0), 2)
            tekanan_reactor1 = round(random.uniform(1.0, 5.0), 2)
            tekanan_reactor2 = round(random.uniform(1.0, 5.0), 2)
            suhu_vessel1 = round(random.uniform(25.0, 85.0), 2)
            suhu_vessel2 = round(random.uniform(25.0, 85.0), 2)
            tekanan_vessel1 = round(random.uniform(1.0, 5.0), 2)
            tekanan_vessel2 = round(random.uniform(1.0, 5.0), 2)
            slurry_flowp1 = round(random.uniform(0.0, 100.0), 2)
            slurry_flowp2 = round(random.uniform(0.0, 100.0), 2)
            slurry_flowp_b1 = round(random.uniform(0.0, 100.0), 2)
            slurry_flowp_b2 = round(random.uniform(0.0, 100.0), 2)
            slurry_flowp_v1 = round(random.uniform(0.0, 100.0), 2)
            slurry_flowp_v2 = round(random.uniform(0.0, 100.0), 2)
            status = random.choice([0, 1])


            # Contoh publish ke peralatan (gunakan nilai yang sama)
            mqtt_client.send_message(TOPIC_PREHEATER1_SUHU, suhu_preheater1)
            mqtt_client.send_message(TOPIC_PREHEATER1_TEKANAN, tekanan_preheater1)
            mqtt_client.send_message(TOPIC_PREHEATER1_STATUS, status)

            mqtt_client.send_message(TOPIC_PREHEATER2_SUHU, suhu_preheater2)
            mqtt_client.send_message(TOPIC_PREHEATER2_TEKANAN, tekanan_preheater2)
            mqtt_client.send_message(TOPIC_PREHEATER2_STATUS, status)

            mqtt_client.send_message(TOPIC_REACTOR1_SUHU, suhu_reactor1)
            mqtt_client.send_message(TOPIC_REACTOR1_TEKANAN, tekanan_reactor1)
            mqtt_client.send_message(TOPIC_REACTOR1_STATUS, status)

            mqtt_client.send_message(TOPIC_REACTOR2_SUHU, suhu_reactor2)
            mqtt_client.send_message(TOPIC_REACTOR2_TEKANAN, tekanan_reactor2)
            mqtt_client.send_message(TOPIC_REACTOR2_STATUS, status)

            mqtt_client.send_message(TOPIC_VESSEL1_SUHU, suhu_vessel1)
            mqtt_client.send_message(TOPIC_VESSEL1_TEKANAN, tekanan_vessel1)
            mqtt_client.send_message(TOPIC_VESSEL1_STATUS, status)

            mqtt_client.send_message(TOPIC_VESSEL2_SUHU, suhu_vessel2)
            mqtt_client.send_message(TOPIC_VESSEL2_TEKANAN, tekanan_vessel2)
            mqtt_client.send_message(TOPIC_VESSEL2_STATUS, status)

            mqtt_client.send_message(TOPIC_SLURRY_FLOWP_P1, slurry_flowp1)
            mqtt_client.send_message(TOPIC_SLURRY_FLOWP_P2, slurry_flowp2)
            mqtt_client.send_message(TOPIC_SLURRY_FLOWP_B1, slurry_flowp_b1)
            mqtt_client.send_message(TOPIC_SLURRY_FLOWP_B2, slurry_flowp_b2)
            mqtt_client.send_message(TOPIC_SLURRY_FLOWP_V1, slurry_flowp_v1)
            mqtt_client.send_message(TOPIC_SLURRY_FLOWP_V2, slurry_flowp_v2)
            
            
            # Tampilkan data yang dikirim (satu baris ringkas)
            status_text = "ON" if status == 1 else "OFF"
            print(
                "\n📊 Data sensor terkirim | "
                f"PH1 {suhu_preheater1}C {tekanan_preheater1}bar {status_text} | "
                f"PH2 {suhu_preheater2}C {tekanan_preheater2}bar {status_text} | "
                f"B1 {suhu_reactor1}C {tekanan_reactor1}bar {status_text} | "
                f"B2 {suhu_reactor2}C {tekanan_reactor2}bar {status_text} | "
                f"V1 {suhu_vessel1}C {tekanan_vessel1}bar {status_text} | "
                f"V2 {suhu_vessel2}C {tekanan_vessel2}bar {status_text} | "
                f"SlurryP1 {slurry_flowp1}% | SlurryP2 {slurry_flowp2}% | "
                f"SlurryB1 {slurry_flowp_b1}% | SlurryB2 {slurry_flowp_b2}% | "
                f"SlurryV1 {slurry_flowp_v1}% | SlurryV2 {slurry_flowp_v2}%"
            )

            # mengambil data setpoint dari AVEVA (jika ada)
            if (
                setpoint_suhu_preheater1 is not None
                or setpoint_suhu_preheater2 is not None
                or setpoint_suhu_reactor1 is not None
                or setpoint_suhu_reactor2 is not None
                or setpoint_pump_acid is not None
                or setpoint_pump_slurry is not None
            ):
                print(f"\n🎯 Setpoint dari AVEVA:")
                if setpoint_suhu_preheater1 is not None:
                    print(f"  - Setpoint suhu preheater 1: {setpoint_suhu_preheater1} °C")
                if setpoint_suhu_preheater2 is not None:
                    print(f"  - Setpoint suhu preheater 2: {setpoint_suhu_preheater2} °C")
                if setpoint_suhu_reactor1 is not None:
                    print(f"  - Setpoint suhu reactor 1: {setpoint_suhu_reactor1} °C")
                if setpoint_suhu_reactor2 is not None:
                    print(f"  - Setpoint suhu reactor 2: {setpoint_suhu_reactor2} °C")
                if setpoint_pump_acid is not None:
                    print(f"  - Perintah pump acid: {setpoint_pump_acid}")
                if setpoint_pump_slurry is not None:
                    print(f"  - Perintah pump slurry: {setpoint_pump_slurry}")
            print()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🔌 Koneksi MQTT dihentikan.")
        client.loop_stop()
        client.disconnect()