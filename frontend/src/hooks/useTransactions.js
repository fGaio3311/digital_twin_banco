import { useState, useCallback } from 'react';
import api from '../api';

export function useTransactions() {
  const [error, setError] = useState(null);

  const deposit = useCallback(
    async (amount) => {
      setError(null);
      try {
        const resp = await api.post(
          '/deposit',
          { amount }
        );
        return resp.data.balance;       // retorna novo saldo
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
        throw err;
      }
    },
    []
  );

  const pix = useCallback(
    async (toUser, amount) => {
      setError(null);
      try {
        const resp = await api.post(
          '/pix',
          { to_user: toUser, amount }
        );
        return resp.data.balance;       // retorna novo saldo do remetente
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
        throw err;
      }
    },
    []
  );

  return { deposit, pix, error };
}
