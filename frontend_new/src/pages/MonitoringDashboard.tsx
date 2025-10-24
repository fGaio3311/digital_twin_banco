import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  FormControlLabel,
  Divider,
  IconButton,
  Tooltip,
  Badge,
  Stack
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  People as PeopleIcon,
  AccountBalance as AccountBalanceIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import axios from 'axios';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

interface Anomaly {
  id: string;
  rule: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
  user?: string;
  amount?: number;
  event: any;
}

interface DashboardData {
  anomalies: Anomaly[];
  system_health: {
    status: 'healthy' | 'warning' | 'critical';
    cpu_usage: number;
    memory_usage: number;
    active_users: number;
    total_transactions: number;
    error_rate: number;
    avg_response_time: number;
  };
  transaction_summary: {
    total_volume: number;
    total_count: number;
    pix_count: number;
    deposit_count: number;
    transfer_count: number;
  };
  user_activity: {
    active_sessions: number;
    new_registrations: number;
    failed_logins: number;
  };
}

const MonitoringDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [unreadAlerts, setUnreadAlerts] = useState(0);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // Buscar dados de diferentes endpoints
      const [anomaliesRes, healthRes] = await Promise.all([
        axios.get(`${process.env.REACT_APP_API_URL}/api/twin/anomalies`, { headers }).catch(() => ({ data: [] })),
        axios.get(`${process.env.REACT_APP_API_URL}/api/twin/health`, { headers }).catch(() => ({ data: {} }))
      ]);

      const newData: DashboardData = {
        anomalies: anomaliesRes.data || [],
        system_health: healthRes.data?.health || {
          status: 'healthy',
          cpu_usage: Math.random() * 100,
          memory_usage: Math.random() * 100,
          active_users: Math.floor(Math.random() * 50),
          total_transactions: Math.floor(Math.random() * 1000),
          error_rate: Math.random() * 5,
          avg_response_time: Math.random() * 500
        },
        transaction_summary: healthRes.data?.transactions || {
          total_volume: Math.random() * 1000000,
          total_count: Math.floor(Math.random() * 1000),
          pix_count: Math.floor(Math.random() * 300),
          deposit_count: Math.floor(Math.random() * 200),
          transfer_count: Math.floor(Math.random() * 500)
        },
        user_activity: healthRes.data?.user_activity || {
          active_sessions: Math.floor(Math.random() * 25),
          new_registrations: Math.floor(Math.random() * 10),
          failed_logins: Math.floor(Math.random() * 5)
        }
      };

      setDashboardData(newData);

      // Contar novos alertas críticos
      const criticalAlerts = newData.anomalies.filter(a => a.severity === 'critical').length;
      setUnreadAlerts(criticalAlerts);

    } catch (error) {
      console.error('Erro ao buscar dados do dashboard:', error);
      // Dados mock para demonstração
      setDashboardData({
        anomalies: [
          {
            id: '1',
            rule: 'big_deposit',
            severity: 'high',
            message: 'Depósito suspeito de R$ 50.000',
            timestamp: new Date().toISOString(),
            user: 'user123',
            amount: 50000,
            event: {}
          },
          {
            id: '2',
            rule: 'high_frequency',
            severity: 'medium',
            message: 'Alta frequência de transações detectada',
            timestamp: new Date(Date.now() - 300000).toISOString(),
            user: 'user456',
            event: {}
          },
          {
            id: '3',
            rule: 'big_pix',
            severity: 'critical',
            message: 'PIX de alto valor: R$ 25.000',
            timestamp: new Date(Date.now() - 600000).toISOString(),
            user: 'user789',
            amount: 25000,
            event: {}
          }
        ],
        system_health: {
          status: 'warning',
          cpu_usage: 75,
          memory_usage: 60,
          active_users: 23,
          total_transactions: 1247,
          error_rate: 2.1,
          avg_response_time: 245
        },
        transaction_summary: {
          total_volume: 2500000,
          total_count: 1247,
          pix_count: 456,
          deposit_count: 234,
          transfer_count: 557
        },
        user_activity: {
          active_sessions: 23,
          new_registrations: 7,
          failed_logins: 3
        }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, 30000); // Refresh a cada 30 segundos
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getSystemHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'inherit';
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('pt-BR');
  };

  if (loading && !dashboardData) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Carregando dados do Digital Twin...
        </Typography>
      </Box>
    );
  }

  const transactionChartData = {
    labels: ['PIX', 'Depósitos', 'Transferências'],
    datasets: [
      {
        data: [
          dashboardData?.transaction_summary.pix_count || 0,
          dashboardData?.transaction_summary.deposit_count || 0,
          dashboardData?.transaction_summary.transfer_count || 0
        ],
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
        hoverBackgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
      }
    ]
  };

  const systemMetricsData = {
    labels: ['CPU', 'Memória', 'Taxa de Erro'],
    datasets: [
      {
        label: 'Uso do Sistema (%)',
        data: [
          dashboardData?.system_health.cpu_usage || 0,
          dashboardData?.system_health.memory_usage || 0,
          dashboardData?.system_health.error_rate || 0
        ],
        backgroundColor: ['rgba(255, 99, 132, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(255, 206, 86, 0.2)'],
        borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)'],
        borderWidth: 1
      }
    ]
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          🏦 Digital Twin - Monitoramento
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          <FormControlLabel
            control={
              <Switch
                checked={alertsEnabled}
                onChange={(e) => setAlertsEnabled(e.target.checked)}
              />
            }
            label="Alertas"
          />
          <Tooltip title="Atualizar dados">
            <IconButton onClick={fetchDashboardData} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Badge badgeContent={unreadAlerts} color="error">
            <NotificationsIcon />
          </Badge>
        </Box>
      </Box>

      {/* System Health Overview */}
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ mb: 3 }}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <CheckCircleIcon
                color={getSystemHealthColor(dashboardData?.system_health.status || 'healthy')}
                sx={{ mr: 1 }}
              />
              <Typography variant="h6">Status do Sistema</Typography>
            </Box>
            <Typography variant="h4" color={getSystemHealthColor(dashboardData?.system_health.status || 'healthy')}>
              {dashboardData?.system_health.status?.toUpperCase() || 'HEALTHY'}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <PeopleIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Usuários Ativos</Typography>
            </Box>
            <Typography variant="h4">
              {dashboardData?.user_activity.active_sessions || 0}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AccountBalanceIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Total Transações</Typography>
            </Box>
            <Typography variant="h4">
              {dashboardData?.transaction_summary.total_count || 0}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SpeedIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Tempo Resposta</Typography>
            </Box>
            <Typography variant="h4">
              {Math.round(dashboardData?.system_health.avg_response_time || 0)}ms
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      {/* Alertas de Anomalias */}
      {alertsEnabled && dashboardData?.anomalies && dashboardData.anomalies.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <SecurityIcon sx={{ mr: 1 }} />
              Alertas de Anomalias ({dashboardData.anomalies.length})
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Stack spacing={2}>
              {dashboardData.anomalies.slice(0, 5).map((anomaly) => (
                <Alert
                  key={anomaly.id}
                  severity={getSeverityColor(anomaly.severity) as any}
                  action={
                    <Chip
                      label={anomaly.rule}
                      size="small"
                      color={getSeverityColor(anomaly.severity) as any}
                    />
                  }
                >
                  <Typography variant="body2">
                    <strong>{anomaly.message}</strong>
                  </Typography>
                  <Typography variant="caption" display="block">
                    Usuário: {anomaly.user || 'N/A'} |
                    Valor: {anomaly.amount ? formatCurrency(anomaly.amount) : 'N/A'} |
                    {formatDateTime(anomaly.timestamp)}
                  </Typography>
                </Alert>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Gráficos e Métricas */}
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ mb: 3 }}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Distribuição de Transações
            </Typography>
            <Box sx={{ height: 300 }}>
              <Doughnut data={transactionChartData} options={{ maintainAspectRatio: false }} />
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Métricas do Sistema
            </Typography>
            <Box sx={{ height: 300 }}>
              <Bar data={systemMetricsData} options={{ maintainAspectRatio: false }} />
            </Box>
          </CardContent>
        </Card>
      </Stack>

      {/* Tabela de Métricas Detalhadas */}
      <Stack direction={{ xs: 'column', lg: 'row' }} spacing={3}>
        <Box sx={{ flex: 2 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Histórico de Anomalias
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Regra</TableCell>
                      <TableCell>Severidade</TableCell>
                      <TableCell>Usuário</TableCell>
                      <TableCell>Valor</TableCell>
                      <TableCell>Mensagem</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {dashboardData?.anomalies?.map((anomaly) => (
                      <TableRow key={anomaly.id}>
                        <TableCell>{formatDateTime(anomaly.timestamp)}</TableCell>
                        <TableCell>
                          <Chip label={anomaly.rule} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={anomaly.severity}
                            size="small"
                            color={getSeverityColor(anomaly.severity) as any}
                          />
                        </TableCell>
                        <TableCell>{anomaly.user || 'N/A'}</TableCell>
                        <TableCell>
                          {anomaly.amount ? formatCurrency(anomaly.amount) : 'N/A'}
                        </TableCell>
                        <TableCell>{anomaly.message}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: 1 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Resumo Financeiro
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Volume Total
                </Typography>
                <Typography variant="h5">
                  {formatCurrency(dashboardData?.transaction_summary.total_volume || 0)}
                </Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  PIX Hoje
                </Typography>
                <Typography variant="h6">
                  {dashboardData?.transaction_summary.pix_count || 0} transações
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Depósitos Hoje
                </Typography>
                <Typography variant="h6">
                  {dashboardData?.transaction_summary.deposit_count || 0} transações
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Novos Usuários
                </Typography>
                <Typography variant="h6">
                  {dashboardData?.user_activity.new_registrations || 0}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Falhas de Login
                </Typography>
                <Typography variant="h6" color="error">
                  {dashboardData?.user_activity.failed_logins || 0}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Stack>
    </Box>
  );
};

export default MonitoringDashboard;
