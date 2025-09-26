import ssl, json, csv
from paho.mqtt import client as mqtt

HOST  = "48dc58d1ec874196bad88e5cee2158b3.s1.eu.hivemq.cloud"
PORT  = 8883
USER  = "nano33"
PASS  = "Atharva1234"   # your HiveMQ password
TOPIC = "gyro/#"
CID   = "py-viewer-01"

# Open CSV once, keep writer around
f = open("gyro_data.csv", "a", newline="")
writer = csv.writer(f)
writer.writerow(["x", "y", "z"])  # header row

def on_connect(c, u, flags, rc, props=None):
    print("on_connect rc:", rc)
    if rc == 0:
        c.subscribe(TOPIC)
        print("✅ Subscribed to", TOPIC)
    else:
        print("❌ Auth failed (rc=%s)" % rc)

def on_message(c, u, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"Got data: x={data['x']}, y={data['y']}, z={data['z']}")
        writer.writerow([data['x'], data['y'], data['z']])
        f.flush()  # make sure it’s saved immediately
    except Exception as e:
        print("⚠️ Error parsing message:", e)

client = mqtt.Client(client_id=CID, protocol=mqtt.MQTTv5, transport="tcp")
client.username_pw_set(USER, PASS)
client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
client.tls_insecure_set(False)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting…")
client.connect(HOST, PORT, keepalive=30)
client.loop_forever()
