import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import { subscribe } from '../mqttService';
import './Dashboard.css';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [seasonality, setSeasonality] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const headers = { Authorization: `Bearer ${token}` };

        const summaryRes = await axios.get('/digital-twin/summary', { headers });
        const anomaliesRes = await axios.get('/digital-twin/anomalies', { headers });
        const seasonalityRes = await axios.get('/digital-twin/sazonalidade', { headers });

        setSummary(summaryRes.data);
        setAnomalies(anomaliesRes.data);
        setSeasonality(seasonalityRes.data);
      } catch (error) {
        setError('Erro ao buscar dados do Digital Twin. Verifique sua autenticação.');
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchData();
    } else {
      setError('Você precisa estar autenticado para acessar o dashboard.');
      setLoading(false);
    }

    subscribe('banco/+/events', (event) => {
      setAnomalies((prev) => [event, ...prev]);
    });
  }, [token]);

  const filteredAnomalies = anomalies.filter((anom) =>
    JSON.stringify(anom).toLowerCase().includes(filter.toLowerCase())
  );

  const exportData = () => {
    const data = {
      summary,
      anomalies: filteredAnomalies,
      seasonality,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'digital_twin_data.json';
    link.click();
  };

  if (loading) return <div className="loading">Carregando...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Banco Digital Twin</h1>
        <button className="export-button" onClick={exportData}>Exportar Dados</button>
      </header>

      <div className="filter-container">
        <input
          type="text"
          placeholder="Filtrar anomalias..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="filter-input"
        />
      </div>

      <main className="dashboard-main">
        {summary && (
          <section className="summary-section">
            <h2>Resumo</h2>
            <pre>{JSON.stringify(summary, null, 2)}</pre>
          </section>
        )}

        {filteredAnomalies.length > 0 && (
          <section className="anomalies-section">
            <h2>Anomalias</h2>
            <ul>
              {filteredAnomalies.map((anom, index) => (
                <li key={index}>{JSON.stringify(anom)}</li>
              ))}
            </ul>
          </section>
        )}

        {seasonality && (
          <section className="seasonality-section">
            <h2>Sazonalidade</h2>
            <Bar
              data={{
                labels: Object.keys(seasonality.by_hour),
                datasets: [
                  {
                    label: 'Atividades por Hora',
                    data: Object.values(seasonality.by_hour),
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                  },
                ],
              }}
            />
          </section>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
