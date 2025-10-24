import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  LinearProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  AppBar,
  Toolbar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  CircularProgress,
  Container
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Download,
  Settings,
  Timeline,
  Speed,
  BugReport,
  CheckCircle,
  Error,
  Warning,
  ExpandMore,
  Visibility,
  Dashboard,
  AdminPanelSettings,
  Assessment,
  Security,
  TrendingUp,
  Memory,
  Storage,
  NetworkCheck,
  Psychology,
  Engineering,
  Business,
  Functions,
  Code,
  Menu,
  Close
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  RadialBarChart,
  RadialBar
} from 'recharts';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

interface LoadTestResult {
  timestamp: string;
  users: number;
  rps: number;
  response_time_avg: number;
  response_time_p95: number;
  response_time_p99: number;
  error_rate: number;
  total_requests: number;
  failed_requests: number;
}

interface SystemStatus {
  timestamp: string;
  digital_twin: any;
  load_testing: any;
  system_metrics: any;
}

const AdminDashboard: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [testResults, setTestResults] = useState<LoadTestResult[]>([]);
  const [integrationResults, setIntegrationResults] = useState<any[]>([]);
  const [realTimeData, setRealTimeData] = useState<LoadTestResult | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [testProgress, setTestProgress] = useState(0);

  const [testConfig, setTestConfig] = useState({
    users: 100,
    spawn_rate: 10,
    duration: 300,
    host: API_BASE_URL,
    run_time: '5m'
  });

  const [predefinedScenarios] = useState([
    {
      name: 'Light Load',
      users: 50,
      spawn_rate: 5,
      duration: 180,
      description: 'Teste leve para verificação básica'
    },
    {
      name: 'Normal Load',
      users: 100,
      spawn_rate: 10,
      duration: 300,
      description: 'Carga normal de operação'
    },
    {
      name: 'Heavy Load',
      users: 500,
      spawn_rate: 50,
      duration: 600,
      description: 'Teste de estresse pesado'
    },
    {
      name: 'Digital Twin Focus',
      users: 200,
      spawn_rate: 20,
      duration: 900,
      description: 'Focado nos endpoints do Digital Twin'
    }
  ]);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 10000); // Atualizar a cada 10 segundos

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/system-status`);
      setSystemStatus(response.data);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const startLoadTest = async () => {
    try {
      setIsTestRunning(true);
      setTestProgress(0);
      setTestResults([]);

      const response = await axios.post(`${API_BASE_URL}/api/admin/load-test/start`, testConfig);

      if (response.data.success) {
        startWebSocketConnection();

        const progressInterval = setInterval(() => {
          setTestProgress(prev => {
            if (prev >= 100) {
              clearInterval(progressInterval);
              return 100;
            }
            return prev + (100 / testConfig.duration);
          });
        }, 1000);

        setTimeout(() => {
          clearInterval(progressInterval);
          setIsTestRunning(false);
          fetchTestResults();
        }, testConfig.duration * 1000);
      }
    } catch (error) {
      console.error('Error starting load test:', error);
      setIsTestRunning(false);
    }
  };

  const stopLoadTest = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/admin/load-test/stop`);
      setIsTestRunning(false);
      setTestProgress(0);
      if (wsRef.current) {
        wsRef.current.close();
      }
    } catch (error) {
      console.error('Error stopping load test:', error);
    }
  };

  const startWebSocketConnection = () => {
    const ws = new WebSocket(`ws://localhost:8001/api/admin/load-test/stream`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRealTimeData(data);
      setTestResults(prev => [...prev, data]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };
  };

  const fetchTestResults = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/load-test/results`);
      setTestResults(response.data.results || []);
    } catch (error) {
      console.error('Error fetching test results:', error);
    }
  };

  const runIntegrationTests = async () => {
    try {
      setIntegrationResults([]);
      const response = await axios.post(`${API_BASE_URL}/api/admin/integration-tests/run`);
      setIntegrationResults(response.data.results || []);
    } catch (error) {
      console.error('Error running integration tests:', error);
    }
  };

  const runAcceptanceTests = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/admin/acceptance-tests/run`);
      console.log('Acceptance tests completed:', response.data);
    } catch (error) {
      console.error('Error running acceptance tests:', error);
    }
  };

  const renderSystemOverview = () => {
    if (!systemStatus) return <CircularProgress />;

    const { system_metrics, digital_twin } = systemStatus;

    return (
      <Grid container spacing={3}>
        {/* System Performance Cards */}
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Memory sx={{ mr: 1 }} />
                <Typography variant="h6">CPU Usage</Typography>
              </Box>
              <Typography variant="h3">{system_metrics.cpu_percent?.toFixed(1)}%</Typography>
              <LinearProgress
                variant="determinate"
                value={system_metrics.cpu_percent}
                sx={{ mt: 1, backgroundColor: 'rgba(255,255,255,0.3)' }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Storage sx={{ mr: 1 }} />
                <Typography variant="h6">Memory</Typography>
              </Box>
              <Typography variant="h3">{system_metrics.memory_percent?.toFixed(1)}%</Typography>
              <LinearProgress
                variant="determinate"
                value={system_metrics.memory_percent}
                sx={{ mt: 1, backgroundColor: 'rgba(255,255,255,0.3)' }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <NetworkCheck sx={{ mr: 1 }} />
                <Typography variant="h6">Connections</Typography>
              </Box>
              <Typography variant="h3">{system_metrics.active_connections}</Typography>
              <Typography variant="body2">Active connections</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Assessment sx={{ mr: 1 }} />
                <Typography variant="h6">Processes</Typography>
              </Box>
              <Typography variant="h3">{system_metrics.running_processes}</Typography>
              <Typography variant="body2">Running processes</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Digital Twin Health */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Psychology sx={{ mr: 1 }} />
                Digital Twin Health Overview
              </Typography>

              <Grid container spacing={2}>
                {Object.entries(digital_twin).map(([key, value]: [string, any]) => (
                  <Grid item xs={12} md={2.4} key={key}>
                    <Paper
                      sx={{
                        p: 2,
                        textAlign: 'center',
                        backgroundColor: value.status === 'healthy' ? '#e8f5e8' : '#fff3e0'
                      }}
                    >
                      <Typography variant="h6" sx={{ textTransform: 'capitalize', fontSize: '0.9rem' }}>
                        {key.replace('_', ' ')}
                      </Typography>
                      <Chip
                        icon={value.status === 'healthy' ? <CheckCircle /> : <Warning />}
                        label={value.status || 'unknown'}
                        color={value.status === 'healthy' ? 'success' : 'warning'}
                        size="small"
                      />
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderLoadTestInterface = () => (
    <Grid container spacing={3}>
      {/* Test Configuration */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <Speed sx={{ mr: 1 }} />
              Load Test Configuration
            </Typography>

            <FormControl fullWidth margin="normal">
              <InputLabel>Predefined Scenario</InputLabel>
              <Select
                value={predefinedScenarios.find(s => s.users === testConfig.users)?.name || ''}
                onChange={(e) => {
                  const scenario = predefinedScenarios.find(s => s.name === e.target.value);
                  if (scenario) {
                    setTestConfig({
                      users: scenario.users,
                      spawn_rate: scenario.spawn_rate,
                      duration: scenario.duration,
                      host: API_BASE_URL,
                      run_time: `${scenario.duration}s`
                    });
                  }
                }}
              >
                {predefinedScenarios.map((scenario) => (
                  <MenuItem key={scenario.name} value={scenario.name}>
                    <Box>
                      <Typography variant="body1">{scenario.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {scenario.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Number of Users"
              type="number"
              value={testConfig.users}
              onChange={(e) => setTestConfig({...testConfig, users: parseInt(e.target.value)})}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Spawn Rate (users/sec)"
              type="number"
              value={testConfig.spawn_rate}
              onChange={(e) => setTestConfig({...testConfig, spawn_rate: parseInt(e.target.value)})}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Duration (seconds)"
              type="number"
              value={testConfig.duration}
              onChange={(e) => setTestConfig({...testConfig, duration: parseInt(e.target.value)})}
              margin="normal"
            />

            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={startLoadTest}
                disabled={isTestRunning}
                fullWidth
                sx={{ mb: 1 }}
                size="large"
              >
                Start Load Test
              </Button>

              {isTestRunning && (
                <Button
                  variant="outlined"
                  startIcon={<Stop />}
                  onClick={stopLoadTest}
                  fullWidth
                  color="error"
                >
                  Stop Test
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Real-time Metrics */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <Timeline sx={{ mr: 1 }} />
              Real-time Performance Metrics
            </Typography>

            {isTestRunning && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Test Progress: {Math.round(testProgress)}%
                </Typography>
                <LinearProgress variant="determinate" value={testProgress} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
            )}

            {realTimeData && (
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                    <Typography variant="h4">{realTimeData.users}</Typography>
                    <Typography variant="caption">Active Users</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white' }}>
                    <Typography variant="h4">{realTimeData.rps.toFixed(1)}</Typography>
                    <Typography variant="caption">RPS</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                    <Typography variant="h4">{realTimeData.response_time_avg.toFixed(0)}ms</Typography>
                    <Typography variant="caption">Avg Response</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={3}>
                  <Paper sx={{
                    p: 2,
                    textAlign: 'center',
                    background: realTimeData.error_rate > 5
                      ? 'linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%)'
                      : 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                    color: 'white'
                  }}>
                    <Typography variant="h4">{realTimeData.error_rate.toFixed(1)}%</Typography>
                    <Typography variant="caption">Error Rate</Typography>
                  </Paper>
                </Grid>
              </Grid>
            )}

            {testResults.length > 0 && (
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={testResults}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="response_time_avg" stroke="#8884d8" name="Avg Response Time (ms)" strokeWidth={2} />
                  <Line yAxisId="left" type="monotone" dataKey="response_time_p95" stroke="#82ca9d" name="95th Percentile (ms)" strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="rps" stroke="#ffc658" name="Requests/sec" strokeWidth={2} />
                  <Area yAxisId="right" type="monotone" dataKey="users" fill="#ff7300" fillOpacity={0.3} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Test Results Summary */}
      {testResults.length > 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Load Test Results Summary</Typography>
                <Button startIcon={<Download />} variant="outlined">
                  Export Results
                </Button>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>Response Time Distribution</Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={testResults.slice(-10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="response_time_avg" fill="#8884d8" name="Avg" />
                      <Bar dataKey="response_time_p95" fill="#82ca9d" name="P95" />
                      <Bar dataKey="response_time_p99" fill="#ffc658" name="P99" />
                    </BarChart>
                  </ResponsiveContainer>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>Error Rate Trend</Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={testResults.slice(-10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis />
                      <Tooltip />
                      <Area type="monotone" dataKey="error_rate" stroke="#ff6b6b" fill="#ff6b6b" fillOpacity={0.6} />
                    </AreaChart>
                  </ResponsiveContainer>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  const renderIntegrationTests = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <BugReport sx={{ mr: 1 }} />
              Integration & Acceptance Tests
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Button
                variant="contained"
                startIcon={<Code />}
                onClick={runIntegrationTests}
                sx={{ mr: 1 }}
              >
                Run Integration Tests
              </Button>
              <Button
                variant="outlined"
                startIcon={<CheckCircle />}
                onClick={runAcceptanceTests}
              >
                Run Acceptance Tests
              </Button>
            </Box>

            {integrationResults.length > 0 && (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Test Name</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Duration (ms)</TableCell>
                      <TableCell>Message</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {integrationResults.map((result, index) => (
                      <TableRow key={index}>
                        <TableCell>{result.test_name}</TableCell>
                        <TableCell>
                          <Chip
                            icon={result.status === 'PASS' ? <CheckCircle /> : result.status === 'FAIL' ? <Error /> : <Warning />}
                            label={result.status}
                            color={result.status === 'PASS' ? "success" : result.status === 'FAIL' ? "error" : "warning"}
                          />
                        </TableCell>
                        <TableCell align="right">{result.duration?.toFixed(0)}</TableCell>
                        <TableCell>{result.message || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const drawerItems = [
    { text: 'System Overview', icon: <Dashboard />, tab: 0 },
    { text: 'Load Testing', icon: <Speed />, tab: 1 },
    { text: 'Integration Tests', icon: <BugReport />, tab: 2 },
    { text: 'Digital Twin Monitor', icon: <Psychology />, tab: 3 },
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={() => setDrawerOpen(!drawerOpen)}
            edge="start"
            sx={{ mr: 2 }}
          >
            <Menu />
          </IconButton>
          <AdminPanelSettings sx={{ mr: 2 }} />
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Digital Twin Admin Dashboard
          </Typography>
          <Badge badgeContent={systemStatus?.load_testing?.is_running ? 'TESTING' : 0} color="error">
            <Assessment />
          </Badge>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        variant="temporary"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        sx={{
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240, mt: 8 },
        }}
      >
        <List>
          {drawerItems.map((item) => (
            <ListItem
              button
              key={item.text}
              onClick={() => {
                setCurrentTab(item.tab);
                setDrawerOpen(false);
              }}
              selected={currentTab === item.tab}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Container maxWidth="xl">
          {currentTab === 0 && renderSystemOverview()}
          {currentTab === 1 && renderLoadTestInterface()}
          {currentTab === 2 && renderIntegrationTests()}
          {currentTab === 3 && (
            <Typography>Digital Twin Monitor Integration (Coming Soon)</Typography>
          )}
        </Container>
      </Box>
    </Box>
  );
};

export default AdminDashboard;
