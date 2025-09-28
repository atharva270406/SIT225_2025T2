# ----- MQTT -> MongoDB Atlas subscriber -----
# pip install -U paho-mqtt pymongo
import ssl, json, csv
from datetime import datetime
from urllib.parse import quote_plus
from paho.mqtt import client as mqtt
from pymongo import MongoClient

# === HiveMQ (same cluster/creds as Arduino) ===
HOST      = "48dc58d1ec874196bad88e5cee2158b3.s1.eu.hivemq.cloud"
PORT      = 8883
MQTT_USER = "nano33"            # <- same as Arduino
MQTT_PASS = "Atharva1234"    # <- same as Arduino
TOPIC     = "gyro/#"
CLIENT_ID = "py-viewer-01"      # unique vs Arduino

# === MongoDB Atlas ===
DB_USER   = "atlasuser"
DB_PASS   = quote_plus("Manit1234")   # encode if special chars
MONGO_URI = f"mongodb+srv://{DB_USER}:{DB_PASS}@cluster0.wyeyq72.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME   = "gyroDB"
COLL_NAME = "samples"

mongo = MongoClient(MONGO_URI)
coll  = mongo[DB_NAME][COLL_NAME]

# Optional local CSV log
csvf = open("gyro_log.csv", "a", newline="")
writer = csv.writer(csvf)
writer.writerow(["ts_iso","x","y","z"])

def on_connect(c, u, flags, rc, props=None):
    print("on_connect rc:", rc)
    if rc == 0:
        c.subscribe(TOPIC)
        print("✅ subscribed to", TOPIC)
    else:
        print("❌ MQTT auth failed (rc=%s)" % rc)

def on_message(c, u, msg):
    try:
        data = json.loads(msg.payload.decode())
        doc = {
            "ts": datetime.utcnow(),
            "x": float(data["x"]),
            "y": float(data["y"]),
            "z": float(data["z"]),
            "topic": msg.topic
        }
        coll.insert_one(doc)                           # save to MongoDB
        writer.writerow([doc["ts"].isoformat(), doc["x"], doc["y"], doc["z"]])
        csvf.flush()
        print(f"{msg.topic}: x={doc['x']:.3f} y={doc['y']:.3f} z={doc['z']:.3f}")
    except Exception as e:
        print("⚠️ parse/store error:", e)

client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5, transport="tcp")
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
client.tls_insecure_set(False)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting MQTT…")
client.connect(HOST, PORT, keepalive=30)
client.loop_forever()

