import json
from datetime import datetime
import paho.mqtt.client as mqtt
from app.settings import mqtt_broker_host, mqtt_broker_port

class MQTTService:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.connect(mqtt_broker_host, mqtt_broker_port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Conectado ao broker MQTT com código: {rc}")

    def publish_balance_update(self, username: str, balance: float, operation_type: str, amount: float):
        payload = {
            "username": username,
            "balance": balance,
            "type": operation_type,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Publica no tópico específico do usuário
        self.client.publish(
            f"digital_twin/{username}/balance",
            json.dumps(payload)
        )

        # Publica no tópico de operações
        self.client.publish(
            f"digital_twin/{username}/operation",
            json.dumps(payload)
        )

mqtt_service = MQTTService()
