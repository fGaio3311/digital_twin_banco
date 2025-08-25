import React, { useState } from 'react';
import { FaMoneyBillWave, FaUserCircle } from 'react-icons/fa';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import './Transfer.css';

const Transfer = () => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    destinationAccount: '',
    amount: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await axios.post('/api/transfer', {
        ...formData,
        amount: parseFloat(formData.amount)
      }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });

      setSuccess(true);
      setFormData({
        destinationAccount: '',
        amount: '',
        description: ''
      });
    } catch (err) {
      setError(err.response?.data?.message || 'Erro ao realizar transferência');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="transfer-container">
      <div className="transfer-card">
        <div className="card-header">
          <FaMoneyBillWave className="header-icon" />
          <h2>Nova Transferência</h2>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {success && (
          <div className="success-message">
            Transferência realizada com sucesso!
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="destinationAccount">Conta de Destino</label>
            <input
              type="text"
              id="destinationAccount"
              name="destinationAccount"
              value={formData.destinationAccount}
              onChange={handleChange}
              required
              placeholder="Número da conta"
            />
          </div>

          <div className="form-group">
            <label htmlFor="amount">Valor</label>
            <div className="amount-input">
              <span>R$</span>
              <input
                type="number"
                id="amount"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                required
                step="0.01"
                min="0.01"
                placeholder="0,00"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="description">Descrição (opcional)</label>
            <input
              type="text"
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Ex: Pagamento aluguel"
            />
          </div>

          <button
            type="submit"
            className="submit-button"
            disabled={loading}
          >
            {loading ? 'Processando...' : 'Confirmar Transferência'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Transfer;
