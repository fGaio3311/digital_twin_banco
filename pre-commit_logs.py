import json
import sys
from datetime import datetime
import paho.mqtt.client as mqtt  # type: ignore[import]

def send_event(event):
    client = mqtt.Client()
    client.connect("localhost", 1883)
    client.publish("banco/precommit/events", json.dumps(event), qos=1)
    client.disconnect()

def main():
    # Recebe o resultado do hook via stdin ou arquivo
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            result = f.read()
    else:
        result = sys.stdin.read()

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "tipo": "code_analysis",
        "info": {
            "result": result
        },
        "descricao": "Resultado do pre-commit"
    }
    send_event(event)

if __name__ == "__main__":
    main()
