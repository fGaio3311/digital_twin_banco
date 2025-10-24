import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Stack,
  Divider,
} from '@mui/material';
import { Person, Save } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';

const Profile: React.FC = () => {
  const { user } = useAuth();
  const { showError, showSuccess } = useNotification();

  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
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

    if (formData.newPassword !== formData.confirmPassword) {
      setError('As senhas não coincidem');
      showError('As senhas não coincidem');
      setLoading(false);
      return;
    }

    if (formData.newPassword.length < 3) {
      setError('A nova senha deve ter pelo menos 3 caracteres');
      showError('A nova senha deve ter pelo menos 3 caracteres');
      setLoading(false);
      return;
    }

    try {
      // Aqui você implementaria a chamada para atualizar a senha
      // await axios.put(`${API_BASE_URL}/profile/password`, formData);

      showSuccess('Senha atualizada com sucesso!');
      setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao atualizar senha';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Meu Perfil
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Gerencie suas informações pessoais e configurações de segurança
      </Typography>

      <Stack spacing={3} sx={{ mt: 3 }}>
        {/* Informações da Conta */}
        <Paper sx={{ p: 4 }}>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <Person color="primary" />
            <Typography variant="h6" fontWeight="bold">
              Informações da Conta
            </Typography>
          </Box>

          <Stack spacing={3}>
            <TextField
              fullWidth
              label="Nome de usuário"
              value={user?.username || ''}
              disabled
              variant="outlined"
            />

            <TextField
              fullWidth
              label="Saldo atual"
              value={`R$ ${user?.balance?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}`}
              disabled
              variant="outlined"
            />
          </Stack>
        </Paper>

        {/* Alterar Senha */}
        <Paper sx={{ p: 4 }}>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Alterar Senha
          </Typography>
          <Divider sx={{ mb: 3 }} />

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <Stack spacing={3}>
              <TextField
                fullWidth
                label="Senha atual"
                name="currentPassword"
                type="password"
                value={formData.currentPassword}
                onChange={handleChange}
                variant="outlined"
              />

              <TextField
                fullWidth
                label="Nova senha"
                name="newPassword"
                type="password"
                value={formData.newPassword}
                onChange={handleChange}
                variant="outlined"
              />

              <TextField
                fullWidth
                label="Confirmar nova senha"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                variant="outlined"
              />

              <Button
                type="submit"
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} /> : <Save />}
                disabled={loading}
                sx={{ py: 1.5, maxWidth: 200 }}
              >
                {loading ? 'Salvando...' : 'Salvar Senha'}
              </Button>
            </Stack>
          </Box>
        </Paper>
      </Stack>
    </Box>
  );
};

export default Profile;
