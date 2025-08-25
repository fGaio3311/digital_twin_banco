import json
import time
import logging
from twin import DigitalTwin
from paho.mqtt import client as mqtt_client
from app.settings import Settings

# Instância das configurações
settings = Settings()

# Logger configurado
logger = logging.getLogger("subscriber")
# Instância do Digital Twin
twin = DigitalTwin()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Configurações via settings.py
BROKER = settings.mqtt_broker_host
PORT = settings.mqtt_broker_port
TOPIC = 'banco/+/events'
CLIENT_ID = f"twin-client-{int(time.time())}"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Conectado ao broker")
        client.subscribe(TOPIC, qos=1)
    else:
        logger.error(f"Erro de conexão: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        ev = json.loads(payload)
        logger.info(f"Evento recebido: {ev}")
        twin.apply_event(ev)
    except Exception as e:
        logger.error(f"Erro ao processar evento: {e}")

def run():
    client = mqtt_client.Client(client_id=CLIENT_ID, protocol=mqtt_client.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_forever()

if __name__ == "__main__":
    run()
