import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

export default function Admin() {
  const [testResults, setTestResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('integration')

  const runIntegrationTests = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/admin/tests/integration`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      setTestResults(response.data.results || [])
    } catch (error) {
      console.error('Erro ao executar testes:', error)
      alert('Erro ao executar testes de integração')
    } finally {
      setLoading(false)
    }
  }

  const runHealthCheck = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/health`)
      setTestResults([{
        test_name: 'Health Check',
        status: response.data.status === 'ok' ? 'PASS' : 'FAIL',
        duration: 0,
        message: `Status: ${response.data.status}`
      }])
    } catch (error) {
      setTestResults([{
        test_name: 'Health Check',
        status: 'FAIL',
        duration: 0,
        message: error.message
      }])
    } finally {
      setLoading(false)
    }
  }

  const getMetrics = async () => {
    try {
      const response = await axios.get(`${API_URL}/metrics`)
      console.log('Métricas:', response.data)
      alert('Métricas obtidas com sucesso. Verifique o console.')
    } catch (error) {
      console.error('Erro ao obter métricas:', error)
      alert('Erro ao obter métricas')
    }
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1>🔧 Painel de Administração</h1>
        <p>Digital Twin + Bank Simulator</p>
      </header>

      <div style={styles.tabs}>
        <button
          style={{...styles.tab, ...(activeTab === 'integration' && styles.tabActive)}}
          onClick={() => setActiveTab('integration')}
        >
          Testes de Integração
        </button>
        <button
          style={{...styles.tab, ...(activeTab === 'health' && styles.tabActive)}}
          onClick={() => setActiveTab('health')}
        >
          Health Check
        </button>
        <button
          style={{...styles.tab, ...(activeTab === 'metrics' && styles.tabActive)}}
          onClick={() => setActiveTab('metrics')}
        >
          Métricas
        </button>
      </div>

      <div style={styles.content}>
        {activeTab === 'integration' && (
          <div>
            <h2>Testes de Integração</h2>
            <button
              style={styles.button}
              onClick={runIntegrationTests}
              disabled={loading}
            >
              {loading ? '⏳ Executando...' : '▶ Executar Testes'}
            </button>
          </div>
        )}

        {activeTab === 'health' && (
          <div>
            <h2>Health Check</h2>
            <button
              style={styles.button}
              onClick={runHealthCheck}
              disabled={loading}
            >
              {loading ? '⏳ Verificando...' : '✓ Verificar Saúde'}
            </button>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div>
            <h2>Métricas Prometheus</h2>
            <button
              style={styles.button}
              onClick={getMetrics}
            >
              📊 Obter Métricas
            </button>
          </div>
        )}

        {testResults.length > 0 && (
          <div style={styles.resultsContainer}>
            <h3>Resultados:</h3>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Teste</th>
                  <th>Status</th>
                  <th>Duração (ms)</th>
                  <th>Mensagem</th>
                </tr>
              </thead>
              <tbody>
                {testResults.map((result, idx) => (
                  <tr key={idx} style={{backgroundColor: result.status === 'PASS' ? '#d4edda' : '#f8d7da'}}>
                    <td>{result.test_name}</td>
                    <td style={{fontWeight: 'bold', color: result.status === 'PASS' ? 'green' : 'red'}}>
                      {result.status}
                    </td>
                    <td>{result.duration?.toFixed(2)}</td>
                    <td>{result.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <footer style={styles.footer}>
        <p>🚀 Sistema em Produção | Backend: {API_URL}</p>
      </footer>
    </div>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
  },
  header: {
    backgroundColor: '#2c3e50',
    color: 'white',
    padding: '30px 20px',
    textAlign: 'center',
  },
  tabs: {
    display: 'flex',
    backgroundColor: '#34495e',
    justifyContent: 'center',
    gap: '0',
    padding: '10px 0',
  },
  tab: {
    backgroundColor: '#34495e',
    color: 'white',
    border: 'none',
    padding: '12px 20px',
    cursor: 'pointer',
    fontSize: '14px',
    borderBottom: '3px solid transparent',
  },
  tabActive: {
    backgroundColor: '#3498db',
    borderBottom: '3px solid #2980b9',
  },
  content: {
    maxWidth: '1000px',
    margin: '30px auto',
    padding: '20px',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  button: {
    backgroundColor: '#3498db',
    color: 'white',
    padding: '12px 24px',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px',
    marginTop: '10px',
    marginBottom: '20px',
  },
  resultsContainer: {
    marginTop: '30px',
    padding: '20px',
    backgroundColor: '#ecf0f1',
    borderRadius: '4px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '10px',
  },
  footer: {
    textAlign: 'center',
    padding: '20px',
    backgroundColor: '#2c3e50',
    color: 'white',
    marginTop: '40px',
  },
}
