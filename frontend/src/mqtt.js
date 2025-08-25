import mqtt from 'mqtt';

class MQTTService {
  constructor() {
    this.client = null;
    this.handlers = new Map();
  }

  connect() {
    this.client = mqtt.connect('ws://localhost:9001'); // WebSocket port do Mosquitto

    this.client.on('connect', () => {
      console.log('Conectado ao MQTT broker');
      this.client.subscribe('digital_twin/#');
    });

    this.client.on('message', (topic, message) => {
      const handlers = this.handlers.get(topic) || [];
      const payload = JSON.parse(message.toString());
      handlers.forEach(handler => handler(payload));
    });
  }

  subscribe(topic, handler) {
    if (!this.handlers.has(topic)) {
      this.handlers.set(topic, []);
    }
    this.handlers.get(topic).push(handler);
  }

  unsubscribe(topic, handler) {
    const handlers = this.handlers.get(topic) || [];
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
    }
  }
}

export const mqttService = new MQTTService();
