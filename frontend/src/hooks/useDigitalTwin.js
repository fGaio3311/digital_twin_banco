import { useEffect, useState } from 'react';
import { mqttService } from '../mqtt';

export function useDigitalTwin() {
  const [balance, setBalance] = useState(null);
  const [lastOperation, setLastOperation] = useState(null);

  useEffect(() => {
    // Conecta ao MQTT ao montar
    mqttService.connect();

    // Subscribe aos tópicos relevantes
    const balanceHandler = (data) => {
      const nextBalance = data?.info?.balance ?? data?.balance ?? null;
      if (typeof nextBalance === 'number') {
        setBalance(nextBalance);
      }
      setLastOperation(data);
    };

    mqttService.subscribe('digital_twin/balance', balanceHandler);
    mqttService.subscribe('digital_twin/operation', balanceHandler);

    return () => {
      mqttService.unsubscribe('digital_twin/balance', balanceHandler);
      mqttService.unsubscribe('digital_twin/operation', balanceHandler);
    };
  }, []);

  return { balance, lastOperation, setBalance, setLastOperation };
}
