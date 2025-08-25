// src/api.js
import axios from 'axios';

// cria a instância apontando para a sua API
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000'
  // removido withCredentials: true pois pode causar problemas com CORS
});

// Melhor tratamento de erros no interceptor
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('Token enviado:', token);
  }
  return config;
}, error => {
  console.error('Erro no interceptor de request:', error);
  return Promise.reject(error);
});

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token'); // limpa token se expirado
    }
    console.error('Erro na resposta:', error);
    throw error;
  }
);

// Funções de autenticação
export const login = async (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  const response = await api.post('/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });

  return response.data.access_token;
};

// registra novo usuário
export async function register(username, password) {
  const { data } = await api.post('/register', { username, password })
  return data
}

// Funções de transação
export const getBalance = async () => {
  const response = await api.get('/balance');
  return response.data.balance;
};

export const deposit = async (amount) => {
  const response = await api.post('/deposit', { amount });
  return response.data.balance;
};

export const pix = async (toUser, amount) => {
  const response = await api.post('/pix', {
    to_user: toUser,
    amount: Number(amount)
  });
  return response.data.balance;
};

// Funções de log
export const getLogs = async () => {
  const response = await api.get('/logs');
  return response.data;
};

export default api;
