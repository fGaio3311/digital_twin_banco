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
  LinearProgress,
  Chip,
} from '@mui/material';
import { AccountBalanceWallet, CheckCircle, Lock, Person } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { showError, showSuccess } = useNotification();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [passwordStrength, setPasswordStrength] = useState(0);

  const calculatePasswordStrength = (password: string): number => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (password.length >= 12) strength += 25;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    return Math.min(strength, 100);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    if (name === 'password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }
  };

  const getPasswordStrengthColor = (strength: number) => {
    if (strength < 25) return 'error';
    if (strength < 50) return 'warning';
    if (strength < 75) return 'info';
    return 'success';
  };

  const getPasswordStrengthLabel = (strength: number) => {
    if (strength < 25) return 'Muito fraca';
    if (strength < 50) return 'Fraca';
    if (strength < 75) return 'Boa';
    return 'Forte';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.username.trim().length < 3) {
      setError('O nome de usuário deve ter pelo menos 3 caracteres');
      showError('O nome de usuário deve ter pelo menos 3 caracteres');
      setLoading(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('As senhas não coincidem');
      showError('As senhas não coincidem');
      setLoading(false);
      return;
    }

    if (formData.password.length < 3) {
      setError('A senha deve ter pelo menos 3 caracteres');
      showError('A senha deve ter pelo menos 3 caracteres');
      setLoading(false);
      return;
    }

    try {
      await register(formData.username, formData.password);
      showSuccess('Conta criada com sucesso!');
      navigate('/dashboard');
    } catch (err: any) {
      const errorMessage = err.message || 'Erro ao criar conta';
      setError(errorMessage);
      showError(errorMessage);
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
      {/* Left side - Benefits */}
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
            Crie sua conta em poucos minutos
          </Typography>
        </Box>

        <Divider sx={{ my: 3, backgroundColor: 'rgba(255,255,255,0.3)', width: '100%' }} />

        <Box sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CheckCircle sx={{ mr: 2, fontSize: 32 }} />
            <Typography variant="body1">
              Registro rápido e fácil
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CheckCircle sx={{ mr: 2, fontSize: 32 }} />
            <Typography variant="body1">
              Acesso imediato ao seu banco
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CheckCircle sx={{ mr: 2, fontSize: 32 }} />
            <Typography variant="body1">
              Segurança e criptografia avançada
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CheckCircle sx={{ mr: 2, fontSize: 32 }} />
            <Typography variant="body1">
              Suporte 24/7 disponível
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Right side - Register Form */}
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
              Crie sua conta bancária digital
            </Typography>
          </Box>

          {/* Alerts */}
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Register Form */}
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            {/* Username Field */}
            <Box sx={{ mb: 2 }}>
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
                InputProps={{
                  startAdornment: <Person sx={{ mr: 1, color: 'primary.main' }} />,
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                Mínimo 3 caracteres
              </Typography>
            </Box>

            {/* Password Field */}
            <Box sx={{ mb: 2 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Senha"
                type="password"
                id="password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
                variant="outlined"
                disabled={loading}
                InputProps={{
                  startAdornment: <Lock sx={{ mr: 1, color: 'primary.main' }} />,
                }}
              />
              {formData.password && (
                <Box sx={{ mt: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Força da senha:
                    </Typography>
                    <Chip
                      label={getPasswordStrengthLabel(passwordStrength)}
                      size="small"
                      color={getPasswordStrengthColor(passwordStrength)}
                      variant="outlined"
                    />
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={passwordStrength}
                    color={getPasswordStrengthColor(passwordStrength)}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                </Box>
              )}
            </Box>

            {/* Confirm Password Field */}
            <Box sx={{ mb: 3 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label="Confirmar Senha"
                type="password"
                id="confirmPassword"
                autoComplete="new-password"
                value={formData.confirmPassword}
                onChange={handleChange}
                variant="outlined"
                disabled={loading}
                error={formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword}
                helperText={
                  formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword
                    ? 'As senhas não coincidem'
                    : ''
                }
                InputProps={{
                  startAdornment: <Lock sx={{ mr: 1, color: 'primary.main' }} />,
                }}
              />
            </Box>

            {/* Submit Button */}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ mt: 2, mb: 2, py: 1.5 }}
              disabled={
                loading ||
                !formData.username ||
                !formData.password ||
                !formData.confirmPassword ||
                formData.password !== formData.confirmPassword
              }
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Criar Conta'}
            </Button>

            {/* Login Link */}
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Já tem uma conta?{' '}
                <Link
                  component="button"
                  variant="body2"
                  onClick={() => navigate('/login')}
                  type="button"
                  sx={{ fontWeight: 'bold' }}
                >
                  Faça login
                </Link>
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default Register;
