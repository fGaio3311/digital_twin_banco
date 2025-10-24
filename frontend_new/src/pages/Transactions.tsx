import React, { useState, useEffect, useCallback } from 'react';
import {
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Add,
  Send,
  SwapHoriz,
} from '@mui/icons-material';
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

const Transactions: React.FC = () => {
  const { showError } = useNotification();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTransactions = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/logs`);
      setTransactions(response.data);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
      showError('Erro ao buscar transações');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

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

  const getTransactionType = (tipo: string) => {
    switch (tipo) {
      case 'deposit':
        return 'Depósito';
      case 'pix':
        return 'PIX Enviado';
      default:
        return 'Transação';
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
      <Box>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Extrato de Transações
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Extrato de Transações
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Histórico completo das suas movimentações financeiras
      </Typography>

      <Paper sx={{ mt: 3 }}>
        {transactions.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Descrição</TableCell>
                  <TableCell>Data/Hora</TableCell>
                  <TableCell align="right">Valor</TableCell>
                  <TableCell align="center">Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.map((transaction, index) => (
                  <TableRow key={index} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getTransactionIcon(transaction.tipo)}
                        {getTransactionType(transaction.tipo)}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {transaction.description || 'Sem descrição'}
                    </TableCell>
                    <TableCell>
                      {new Date(transaction.timestamp).toLocaleString('pt-BR')}
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        fontWeight="bold"
                        color={transaction.tipo === 'deposit' ? 'success.main' : 'error.main'}
                      >
                        {transaction.tipo === 'deposit' ? '+' : '-'} R$ {transaction.amount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label="Concluído"
                        size="small"
                        color={getTransactionColor(transaction.tipo) as any}
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box p={4}>
            <Alert severity="info">
              Nenhuma transação encontrada. Faça seu primeiro depósito ou transferência!
            </Alert>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Transactions;
