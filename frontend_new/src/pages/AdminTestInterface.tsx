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
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tabs,
  Tab,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
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
  Visibility
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
  Area
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

interface TestScenario {
  name: string;
  users: number;
  spawn_rate: number;
  duration: number;
  host: string;
  endpoints: string[];
}

interface IntegrationTestResult {
  test_name: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  duration: number;
  message?: string;
  details?: any;
}

const AdminTestInterface: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [testResults, setTestResults] = useState<LoadTestResult[]>([]);
  const [integrationResults, setIntegrationResults] = useState<IntegrationTestResult[]>([]);
  const [realTimeData, setRealTimeData] = useState<LoadTestResult | null>(null);
  const [testProgress, setTestProgress] = useState(0);
  const [selectedScenario, setSelectedScenario] = useState<TestScenario>({
    name: 'Banking Load Test',
    users: 100,
    spawn_rate: 10,
    duration: 300,
    host: API_BASE_URL,
    endpoints: ['/ping', '/balance', '/logs', '/api/twin/dashboard/complete']
  });

  const [testConfig, setTestConfig] = useState({
    users: 100,
    spawn_rate: 10,
    duration: 300,
    host: API_BASE_URL,
    run_time: '5m'
  });

  const [predefinedScenarios] = useState<TestScenario[]>([
    {
      name: 'Light Load',
      users: 50,
      spawn_rate: 5,
      duration: 180,
      host: API_BASE_URL,
      endpoints: ['/ping', '/balance']
    },
    {
      name: 'Normal Load',
      users: 100,
      spawn_rate: 10,
      duration: 300,
      host: API_BASE_URL,
      endpoints: ['/ping', '/balance', '/logs']
    },
    {
      name: 'Heavy Load',
      users: 500,
      spawn_rate: 50,
      duration: 600,
      host: API_BASE_URL,
      endpoints: ['/ping', '/balance', '/logs', '/api/twin/dashboard/complete']
    },
    {
      name: 'Spike Test',
      users: 1000,
      spawn_rate: 100,
      duration: 120,
      host: API_BASE_URL,
      endpoints: ['/ping', '/balance', '/logs', '/pix', '/api/twin/dashboard/complete']
    },
    {
      name: 'Digital Twin Stress',
      users: 200,
      spawn_rate: 20,
      duration: 900,
      host: API_BASE_URL,
      endpoints: [
        '/api/twin/business-drivers',
        '/api/twin/functionality',
        '/api/twin/rnf',
        '/api/twin/engineering',
        '/api/twin/technology',
        '/api/twin/dashboard/complete'
      ]
    }
  ]);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Cleanup WebSocket on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const startLoadTest = async () => {
    try {
      setIsTestRunning(true);
      setTestProgress(0);
      setTestResults([]);

      const response = await axios.post(`${API_BASE_URL}/api/admin/load-test/start`, {
        users: testConfig.users,
        spawn_rate: testConfig.spawn_rate,
        duration: testConfig.duration,
        host: testConfig.host
      });

      if (response.data.success) {
        // Start WebSocket connection for real-time updates
        startWebSocketConnection();

        // Simulate progress
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

  const exportResults = () => {
    const data = JSON.stringify(testResults, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `load_test_results_${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderLoadTestTab = () => (
    <Box>
      <Grid container spacing={3}>
        {/* Test Configuration */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Configuration
              </Typography>

              <FormControl fullWidth margin="normal">
                <InputLabel>Predefined Scenario</InputLabel>
                <Select
                  value={selectedScenario.name}
                  onChange={(e) => {
                    const scenario = predefinedScenarios.find(s => s.name === e.target.value);
                    if (scenario) {
                      setSelectedScenario(scenario);
                      setTestConfig({
                        users: scenario.users,
                        spawn_rate: scenario.spawn_rate,
                        duration: scenario.duration,
                        host: scenario.host,
                        run_time: `${scenario.duration}s`
                      });
                    }
                  }}
                >
                  {predefinedScenarios.map((scenario) => (
                    <MenuItem key={scenario.name} value={scenario.name}>
                      {scenario.name}
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

              <TextField
                fullWidth
                label="Target Host"
                value={testConfig.host}
                onChange={(e) => setTestConfig({...testConfig, host: e.target.value})}
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
              <Typography variant="h6" gutterBottom>
                Real-time Performance Metrics
              </Typography>

              {isTestRunning && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Test Progress: {Math.round(testProgress)}%
                  </Typography>
                  <LinearProgress variant="determinate" value={testProgress} />
                </Box>
              )}

              {realTimeData && (
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={3}>
                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {realTimeData.users}
                      </Typography>
                      <Typography variant="caption">Active Users</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={3}>
                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {realTimeData.rps.toFixed(1)}
                      </Typography>
                      <Typography variant="caption">RPS</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={3}>
                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                      <Typography variant="h4" color="warning.main">
                        {realTimeData.response_time_avg.toFixed(0)}ms
                      </Typography>
                      <Typography variant="caption">Avg Response</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={3}>
                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                      <Typography variant="h4" color={realTimeData.error_rate > 5 ? "error.main" : "success.main"}>
                        {realTimeData.error_rate.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption">Error Rate</Typography>
                    </Paper>
                  </Grid>
                </Grid>
              )}

              {testResults.length > 0 && (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={testResults}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="response_time_avg" stroke="#8884d8" name="Avg Response Time (ms)" />
                    <Line yAxisId="left" type="monotone" dataKey="response_time_p95" stroke="#82ca9d" name="95th Percentile (ms)" />
                    <Line yAxisId="right" type="monotone" dataKey="rps" stroke="#ffc658" name="Requests/sec" />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Test Results Table */}
        {testResults.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Test Results
                  </Typography>
                  <Button
                    startIcon={<Download />}
                    onClick={exportResults}
                    variant="outlined"
                  >
                    Export Results
                  </Button>
                </Box>

                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Time</TableCell>
                        <TableCell align="right">Users</TableCell>
                        <TableCell align="right">RPS</TableCell>
                        <TableCell align="right">Avg Response (ms)</TableCell>
                        <TableCell align="right">95th Percentile (ms)</TableCell>
                        <TableCell align="right">99th Percentile (ms)</TableCell>
                        <TableCell align="right">Error Rate (%)</TableCell>
                        <TableCell align="right">Total Requests</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {testResults.slice(-10).map((result, index) => (
                        <TableRow key={index}>
                          <TableCell>{result.timestamp}</TableCell>
                          <TableCell align="right">{result.users}</TableCell>
                          <TableCell align="right">{result.rps.toFixed(1)}</TableCell>
                          <TableCell align="right">{result.response_time_avg.toFixed(0)}</TableCell>
                          <TableCell align="right">{result.response_time_p95.toFixed(0)}</TableCell>
                          <TableCell align="right">{result.response_time_p99.toFixed(0)}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${result.error_rate.toFixed(1)}%`}
                              color={result.error_rate > 5 ? "error" : "success"}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">{result.total_requests}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  const renderIntegrationTestsTab = () => (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Integration & Acceptance Tests
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<BugReport />}
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
                        <TableCell>Actions</TableCell>
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
                          <TableCell align="right">{result.duration}</TableCell>
                          <TableCell>{result.message || '-'}</TableCell>
                          <TableCell>
                            {result.details && (
                              <IconButton size="small">
                                <Visibility />
                              </IconButton>
                            )}
                          </TableCell>
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
    </Box>
  );

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        Admin Test Interface
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={currentTab}
          onChange={(e, newValue) => setCurrentTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<Speed />} label="Load Testing" />
          <Tab icon={<BugReport />} label="Integration Tests" />
          <Tab icon={<Timeline />} label="Performance Analysis" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {currentTab === 0 && renderLoadTestTab()}
          {currentTab === 1 && renderIntegrationTestsTab()}
          {currentTab === 2 && (
            <Typography>Performance Analysis Dashboard (Coming Soon)</Typography>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default AdminTestInterface;
