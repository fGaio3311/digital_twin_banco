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
} from '@mui/material';
import { Send } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const Transfer: React.FC = () => {
  const { refreshBalance } = useAuth();
  const { showError, showSuccess } = useNotification();

  const [formData, setFormData] = useState({
    toUser: '',
    amount: '',
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

    try {
      await axios.post(`${API_BASE_URL}/pix`, {
        to_user: formData.toUser,
        amount: parseFloat(formData.amount),
      });

      showSuccess('Transferência realizada com sucesso!');
      await refreshBalance();
      setFormData({ toUser: '', amount: '' });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao realizar transferência';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Transferir Dinheiro
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Realize transferências PIX de forma rápida e segura
      </Typography>

      <Paper sx={{ p: 4, mt: 3, maxWidth: 600 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={3}>
            <TextField
              fullWidth
              label="Usuário de destino"
              name="toUser"
              value={formData.toUser}
              onChange={handleChange}
              required
              variant="outlined"
              helperText="Digite o nome do usuário que receberá a transferência"
            />

            <TextField
              fullWidth
              label="Valor"
              name="amount"
              type="number"
              value={formData.amount}
              onChange={handleChange}
              required
              variant="outlined"
              InputProps={{
                startAdornment: <Typography sx={{ mr: 1 }}>R$</Typography>,
              }}
              inputProps={{ min: 0.01, step: 0.01 }}
              helperText="Valor mínimo: R$ 0,01"
            />

            <Button
              type="submit"
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <Send />}
              disabled={loading}
              sx={{ py: 1.5 }}
            >
              {loading ? 'Processando...' : 'Transferir'}
            </Button>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
};

export default Transfer;
