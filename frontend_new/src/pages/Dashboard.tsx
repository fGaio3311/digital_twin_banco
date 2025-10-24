import React, { useState, useEffect, useCallback } from 'react';
import {
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Stack,
} from '@mui/material';
import {
  AccountBalance,
  TrendingUp,
  SwapHoriz,
  Add,
  Send,
  Visibility,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

interface Transaction {
  id: number;
  tipo: string;
  amount: number;
  timestamp: string;
  description?: string;
}

interface QuickAction {
  title: string;
  icon: React.ReactNode;
  color: string;
  action: () => void;
}

const Dashboard: React.FC = () => {
  const { user, refreshBalance } = useAuth();
  const { showError } = useNotification();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTransactions = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/logs`);
      setTransactions(response.data.slice(0, 5)); // Últimas 5 transações
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
      showError('Erro ao buscar transações');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    fetchTransactions();
    refreshBalance();
  }, [fetchTransactions, refreshBalance]);

  const quickActions: QuickAction[] = [
    {
      title: 'Depositar',
      icon: <Add />,
      color: '#4caf50',
      action: () => console.log('Depositar'),
    },
    {
      title: 'Transferir',
      icon: <Send />,
      color: '#2196f3',
      action: () => console.log('Transferir'),
    },
    {
      title: 'Extrato',
      icon: <Visibility />,
      color: '#ff9800',
      action: () => console.log('Extrato'),
    },
  ];

  const getTransactionIcon = (tipo: string) => {
    switch (tipo) {
      case 'deposit':
        return <Add color="success" />;
      case 'pix':
        return <Send color="primary" />;
      default:
        return <SwapHoriz />;
    }
  };

  const getTransactionColor = (tipo: string) => {
    switch (tipo) {
      case 'deposit':
        return 'success';
      case 'pix':
        return 'primary';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Olá, {user?.username}!
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Bem-vindo ao seu painel financeiro
      </Typography>

      <Stack spacing={3} sx={{ mt: 3 }}>
        {/* Linha 1: Saldo e Ações Rápidas */}
        <Box display="flex" gap={3} flexWrap={{ xs: 'wrap', md: 'nowrap' }}>
          {/* Saldo Principal */}
          <Box flex={{ xs: '1 1 100%', md: '1 1 65%' }}>
            <Paper
              sx={{
                p: 3,
                background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
                color: 'white',
                borderRadius: 3,
              }}
            >
              <Box display="flex" alignItems="center" mb={2}>
                <AccountBalance sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography variant="h6">Conta Corrente</Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Saldo disponível
                  </Typography>
                </Box>
              </Box>
              <Typography variant="h3" fontWeight="bold">
                R$ {user?.balance?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </Typography>
              <Box display="flex" gap={2} mt={3}>
                <Button
                  variant="contained"
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' } }}
                  startIcon={<Add />}
                >
                  Depositar
                </Button>
                <Button
                  variant="outlined"
                  sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.5)' }}
                  startIcon={<Send />}
                >
                  Transferir
                </Button>
              </Box>
            </Paper>
          </Box>

          {/* Ações Rápidas */}
          <Box flex={{ xs: '1 1 100%', md: '1 1 35%' }}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Ações Rápidas
              </Typography>
              <Stack spacing={2}>
                {quickActions.map((action, index) => (
                  <Button
                    key={index}
                    variant="outlined"
                    startIcon={action.icon}
                    onClick={action.action}
                    sx={{
                      justifyContent: 'flex-start',
                      color: action.color,
                      borderColor: action.color,
                      '&:hover': {
                        bgcolor: `${action.color}10`,
                        borderColor: action.color,
                      },
                    }}
                  >
                    {action.title}
                  </Button>
                ))}
              </Stack>
            </Paper>
          </Box>
        </Box>

        {/* Linha 2: Resumo e Transações */}
        <Box display="flex" gap={3} flexWrap={{ xs: 'wrap', lg: 'nowrap' }}>
          {/* Resumo de Atividades */}
          <Box flex={{ xs: '1 1 100%', lg: '1 1 50%' }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Resumo Mensal
              </Typography>
              <Box display="flex" gap={2}>
                <Box flex="1">
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <TrendingUp color="success" sx={{ fontSize: 30, mb: 1 }} />
                      <Typography variant="h6" color="success.main">
                        R$ 5.420,00
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Entradas
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                <Box flex="1">
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Send color="primary" sx={{ fontSize: 30, mb: 1 }} />
                      <Typography variant="h6" color="primary.main">
                        R$ 2.180,00
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Saídas
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
              </Box>
            </Paper>
          </Box>

          {/* Últimas Transações */}
          <Box flex={{ xs: '1 1 100%', lg: '1 1 50%' }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Últimas Transações
              </Typography>
              <Box>
                {transactions.length > 0 ? (
                  transactions.map((transaction, index) => (
                    <Box
                      key={index}
                      display="flex"
                      alignItems="center"
                      justifyContent="space-between"
                      py={1.5}
                      borderBottom={index < transactions.length - 1 ? '1px solid #eee' : 'none'}
                    >
                      <Box display="flex" alignItems="center">
                        <Box sx={{ mr: 2 }}>
                          {getTransactionIcon(transaction.tipo)}
                        </Box>
                        <Box>
                          <Typography variant="body1" fontWeight="medium">
                            {transaction.tipo === 'deposit' ? 'Depósito' : 'PIX Enviado'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {new Date(transaction.timestamp).toLocaleString('pt-BR')}
                          </Typography>
                        </Box>
                      </Box>
                      <Box textAlign="right">
                        <Typography
                          variant="body1"
                          fontWeight="bold"
                          color={transaction.tipo === 'deposit' ? 'success.main' : 'error.main'}
                        >
                          {transaction.tipo === 'deposit' ? '+' : '-'} R$ {transaction.amount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </Typography>
                        <Chip
                          label={transaction.tipo === 'deposit' ? 'Entrada' : 'Saída'}
                          size="small"
                          color={getTransactionColor(transaction.tipo) as any}
                          variant="outlined"
                        />
                      </Box>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
                    Nenhuma transação encontrada
                  </Typography>
                )}
              </Box>
            </Paper>
          </Box>
        </Box>
      </Stack>
    </Box>
  );
};

export default Dashboard;
