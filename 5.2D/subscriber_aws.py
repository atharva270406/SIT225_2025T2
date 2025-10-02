#!/usr/bin/env python3
import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from pymongo import MongoClient

import config  # contains credentials

# ---------- MongoDB ----------
mongo_client = MongoClient(config.MONGO_URI)
mongo_col = mongo_client[config.MONGO_DB][config.MONGO_COLLECTION]

# ---------- Optional Redis ----------
use_redis = all(hasattr(config, k) for k in ("REDIS_HOST", "REDIS_PORT", "REDIS_USER", "REDIS_PASS"))
rclient = None

if use_redis:
    try:
        import redis
        # Attempt TLS connection first
        rclient = redis.Redis(
            host=config.REDIS_HOST,
            port=int(config.REDIS_PORT),
            username=getattr(config, "REDIS_USER", None),
            password=config.REDIS_PASS,
            ssl=True,
            ssl_cert_reqs=None,
            socket_timeout=3,
        )
        rclient.ping()
        print("🟥 Redis connected (TLS).")
    except Exception as e_tls:
        print(f"⚠️ TLS Redis connect failed: {e_tls}, trying non-TLS…")
        try:
            rclient = redis.Redis(
                host=config.REDIS_HOST,
                port=int(config.REDIS_PORT),
                username=getattr(config, "REDIS_USER", None),
                password=config.REDIS_PASS,
                ssl=False,
                socket_timeout=3,
            )
            rclient.ping()
            print("🟥 Redis connected (non-TLS).")
        except Exception as e_plain:
            print(f"❌ Redis connect failed: {e_plain}")
            rclient = None
            use_redis = False

# ---------- Helper functions ----------
def save_to_mongo(doc: dict) -> dict:
    """Insert document into MongoDB and return a copy with string _id."""
    doc_copy = dict(doc)
    result = mongo_col.insert_one(doc_copy)
    doc_copy["_id"] = str(result.inserted_id)
    return doc_copy

def save_to_redis(doc: dict):
    if use_redis and rclient:
        rclient.set(doc["ts_iso"], json.dumps(doc, default=str))

# ---------- MQTT callbacks ----------
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("✅ Connected to HiveMQ")
        client.subscribe(config.MQTT_TOPIC, qos=1)
        print(f"📡 Subscribed to: {config.MQTT_TOPIC}")
    else:
        print(f"❌ MQTT connect failed (code={reason_code})")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="replace").strip()
        data = json.loads(payload)

        x, y, z = (float(data[k]) for k in ("x", "y", "z"))
        ts_iso = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        doc = {"ts_iso": ts_iso, "x": x, "y": y, "z": z}

        # Save to MongoDB
        saved_doc = save_to_mongo(doc)

        # Save to Redis if enabled
        if use_redis:
            save_to_redis(doc)
            destinations = "MongoDB & Redis"
        else:
            destinations = "MongoDB"

        print(f"💾 Saved to {destinations}: {saved_doc}")

    except Exception as e:
        print(f"⚠️ Error processing message: {e}")

def on_disconnect(client, userdata, reason_code, properties=None):
    print(f"🔌 Disconnected (code={reason_code})")

# ---------- MQTT Client ----------
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(config.MQTT_USER, config.MQTT_PASS)
mqtt_client.tls_set()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect

print("🚀 Connecting to HiveMQ…")
mqtt_client.connect(config.MQTT_BROKER, int(config.MQTT_PORT), keepalive=60)

try:
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Stopping subscriber…")
finally:
    try:
        mqtt_client.disconnect()
    except Exception:
        pass
    mongo_client.close()
