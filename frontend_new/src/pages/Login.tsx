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
  Divider,
  Card,
  CardContent,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  AccountBalanceWallet,
  CheckCircle,
  VpnKey,
  Security,
  Speed,
} from '@mui/icons-material';
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
  const [showCredentials, setShowCredentials] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const testAccounts = [
    { username: 'admin', password: 'admin123', role: 'Administrador', balance: '10.000,00' },
    { username: 'user1', password: 'user123', role: 'Usuário', balance: '5.000,00' },
    { username: 'user2', password: 'user123', role: 'Usuário', balance: '3.000,00' },
    { username: 'test', password: 'test123', role: 'Teste', balance: '1.000,00' },
  ];

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
      var regex = /[<]*<[\s\u200B]*script[\s\u200B]*>.*[/]*[<]*<[\s\u200B]*\/[\s\u200B]*script[\s\u200B]*>/ig;
      if (!(formData.username.match(regex) || formData.password.match(regex))) {
        await login(formData.username, formData.password);
        if (rememberMe) {
          localStorage.setItem('rememberMe', 'true');
          localStorage.setItem('lastUsername', formData.username);
        } else {
          localStorage.removeItem('rememberMe');
          localStorage.removeItem('lastUsername');
        }
        showSuccess('Login realizado com sucesso!');
        navigate('/dashboard');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage = err.message || 'Erro ao fazer login';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleTestAccountClick = (account: typeof testAccounts[0]) => {
    setFormData({
      username: account.username,
      password: account.password,
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
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
      }}
    >
      {/* Left side - Features */}
      <Box
        sx={{
          flex: 1,
          display: { xs: 'none', md: 'flex' },
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'flex-start',
          padding: 4,
          color: 'white',
        }}
      >
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <AccountBalanceWallet sx={{ fontSize: 48, mr: 2 }} />
            <Typography variant="h3" fontWeight="bold">
              Digital Bank
            </Typography>
          </Box>
          <Typography variant="h6" sx={{ opacity: 0.9 }}>
            A sua solução bancária digital segura e inovadora
          </Typography>
        </Box>

        <Divider sx={{ my: 3, backgroundColor: 'rgba(255,255,255,0.3)', width: '100%' }} />

        <Box sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Security sx={{ mr: 2, fontSize: 32 }} />
            <Box>
              <Typography variant="h6" fontWeight="bold">
                Segurança em Primeiro Lugar
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Autenticação JWT e criptografia de dados
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Speed sx={{ mr: 2, fontSize: 32 }} />
            <Box>
              <Typography variant="h6" fontWeight="bold">
                Transações em Tempo Real
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                MQTT para notificações instantâneas
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <VpnKey sx={{ mr: 2, fontSize: 32 }} />
            <Box>
              <Typography variant="h6" fontWeight="bold">
                Monitoramento Inteligente
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Detecção de anomalias em tempo real
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Right side - Login Form */}
      <Container component="main" maxWidth="sm" sx={{ display: 'flex', alignItems: 'center', py: 4 }}>
        <Paper
          elevation={10}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
            borderRadius: 3,
            background: 'rgba(255, 255, 255, 0.95)',
          }}
        >
          {/* Header */}
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <AccountBalanceWallet sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography component="h1" variant="h4" fontWeight="bold" color="primary">
              Digital Bank
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Acesse sua conta bancária
            </Typography>
          </Box>

          {/* Alerts */}
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Login Form */}
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
              disabled={loading}
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
              disabled={loading}
            />

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', my: 2 }}>
              <Link
                component="button"
                variant="body2"
                type="button"
                onClick={() => navigate('/register')}
              >
                Criar Conta
              </Link>
              <Link href="#" variant="body2">
                Esqueceu a senha?
              </Link>
            </Box>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ mt: 1, mb: 2, py: 1.5 }}
              disabled={loading || !formData.username || !formData.password}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Entrar'}
            </Button>

            <Button
              fullWidth
              variant="outlined"
              onClick={() => setShowCredentials(true)}
              disabled={loading}
              sx={{ mb: 2 }}
            >
              Ver Contas de Teste
            </Button>
          </Box>

          {/* Divider */}
          <Divider sx={{ my: 3, width: '100%' }}>Contas de Teste</Divider>

          {/* Test Accounts Display */}
          <Grid container spacing={1} sx={{ width: '100%' }}>
            {testAccounts.map((account, index) => (
              <Grid item xs={12} sm={6} key={index}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                    backgroundColor: formData.username === account.username ? '#e3f2fd' : 'background.paper',
                  }}
                  onClick={() => handleTestAccountClick(account)}
                >
                  <CardContent sx={{ py: 1.5, px: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {formData.username === account.username && (
                        <CheckCircle sx={{ fontSize: 18, color: 'primary', mr: 1 }} />
                      )}
                      <Chip
                        label={account.role}
                        size="small"
                        color={account.role === 'Administrador' ? 'error' : 'primary'}
                        variant={account.role === 'Administrador' ? 'filled' : 'outlined'}
                      />
                    </Box>
                    <Typography variant="body2" fontWeight="bold" sx={{ mb: 0.5 }}>
                      {account.username}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                      {account.password}
                    </Typography>
                    <Typography variant="caption" color="success.main" fontWeight="bold">
                      R$ {account.balance}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
            Clique em qualquer conta para preencher automaticamente
          </Typography>
        </Paper>
      </Container>

      {/* Credentials Dialog */}
      <Dialog open={showCredentials} onClose={() => setShowCredentials(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <VpnKey sx={{ mr: 2, color: 'primary' }} />
            <Typography variant="h6">Credenciais de Teste</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {testAccounts.map((account, index) => (
            <Card key={index} sx={{ mb: 2, backgroundColor: '#f5f5f5' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6" fontWeight="bold">
                    {account.role}
                  </Typography>
                  <Chip
                    label={account.role === 'Administrador' ? 'Admin' : 'User'}
                    size="small"
                    color={account.role === 'Administrador' ? 'error' : 'primary'}
                  />
                </Box>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Usuário:</strong> {account.username}
                </Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Senha:</strong> {account.password}
                </Typography>
                <Typography variant="body2" color="success.main">
                  <strong>Saldo:</strong> R$ {account.balance}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCredentials(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Login;
