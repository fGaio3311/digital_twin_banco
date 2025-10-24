import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Link,
  Alert,
  CircularProgress,
} from '@mui/material';
import { AccountBalanceWallet } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import axios from 'axios';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { showError, showSuccess } = useNotification();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    console.log('Login attempt:', { username: formData.username, password: formData.password });

    try {
      await login(formData.username, formData.password);
      showSuccess('Login realizado com sucesso!');
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage = err.message || 'Erro ao fazer login';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleTestAccount = () => {
    setFormData({
      username: 'test123',
      password: 'test123',
    });
  };

  const createTestAccount = async () => {
    setLoading(true);
    setError('');

    try {
      console.log('Creating test account...');
      // First try to register the test account
      await axios.post(`${process.env.REACT_APP_API_URL || 'http://localhost:8001'}/register`, {
        username: 'test123',
        password: 'test123'
      });
      showSuccess('Conta de teste criada! Agora você pode fazer login.');
    } catch (err: any) {
      console.log('Test account might already exist, trying to login...');
      // Account might already exist, that's ok
      if (err.response?.status === 400) {
        showSuccess('Conta de teste já existe! Use as credenciais: test123/test123');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
        }}
      >
        <Paper
          elevation={10}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
            maxWidth: 400,
            borderRadius: 3,
          }}
        >
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <AccountBalanceWallet sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography component="h1" variant="h4" fontWeight="bold" color="primary">
              Digital Bank
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Faça login para acessar sua conta
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Nome de usuário"
              name="username"
              autoComplete="username"
              autoFocus
              value={formData.username}
              onChange={handleChange}
              variant="outlined"
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Senha"
              type="password"
              id="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              variant="outlined"
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2, py: 1.5 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Entrar'}
            </Button>

            <Button
              fullWidth
              variant="outlined"
              sx={{ mb: 1 }}
              onClick={handleTestAccount}
              disabled={loading}
            >
              Usar Conta de Teste
            </Button>

            <Button
              fullWidth
              variant="outlined"
              sx={{ mb: 2 }}
              onClick={createTestAccount}
              disabled={loading}
            >
              Criar Conta de Teste
            </Button>

            <Box textAlign="center">
              <Link
                component="button"
                variant="body2"
                onClick={() => navigate('/register')}
                type="button"
              >
                Não tem uma conta? Cadastre-se
              </Link>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
