import json
import logging
from paho.mqtt import client as mqtt_client
from app.settings import Settings

settings = Settings()
logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.client = None
        self._setup()

    def _setup(self):
        try:
            self.client = mqtt_client.Client()
            self.client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
            self.client.loop_start()
            logger.info("Conectado ao MQTT com sucesso.")
        except Exception as e:
            logger.error(f"[MQTT ERRO] Falha ao conectar: {e}")
            self.client = None

    def publish_balance(self, user_name: str, new_balance: float):
        if not self.client:
            return
        ev = {"user": user_name, "balance": new_balance}
        try:
            self.client.publish("digital_twin/balance", json.dumps(ev), qos=1)
        except Exception as e:
            logger.warning(f"Falha ao publicar balance MQTT: {e}")

    def publish_anomaly(self, anomaly_data: dict):
        if not self.client:
            return
        try:
            self.client.publish("digital_twin/anomalies", json.dumps(anomaly_data), qos=0)
        except Exception as e:
            logger.warning(f"Falha ao publicar anomalia MQTT: {e}")

    def publish_operation(self, event_data: dict):
        if not self.client:
            return
        try:
            self.client.publish("digital_twin/operation", json.dumps(event_data), qos=1)
        except Exception as e:
            logger.warning(f"Falha ao publicar operacao MQTT: {e}")

mqtt_service = MQTTService()
