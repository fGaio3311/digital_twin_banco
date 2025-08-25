import { useState } from 'react';
import api from '../api';

export function useAuth() {
  const [user, setUser] = useState(null);

  async function login(username, password) {
    const { data } = await api.post('/token', `username=${username}&password=${password}`, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    localStorage.setItem('token', data.access_token); // padronizado para 'token'
    setUser(username);
  }

  async function register(username, password) {
    await api.post('/register', { username, password });
  }

  function logout() {
    localStorage.removeItem('token'); // padronizado para 'token'
    setUser(null);
  }

  return { user, login, register, logout };
}
