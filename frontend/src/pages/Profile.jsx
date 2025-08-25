import React, { useState } from 'react';
import { FaUser, FaEnvelope, FaKey } from 'react-icons/fa';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import './Profile.css';

const Profile = () => {
  const { user, setUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
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
      if (formData.newPassword && formData.newPassword !== formData.confirmPassword) {
        throw new Error('As senhas não conferem');
      }

      const response = await axios.put('/api/user/profile', formData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });

      setUser(response.data);
      setSuccess(true);
      setEditing(false);
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Erro ao atualizar perfil');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="card-header">
          <FaUser className="header-icon" />
          <h2>Meu Perfil</h2>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {success && (
          <div className="success-message">
            Perfil atualizado com sucesso!
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">
              <FaUser /> Nome
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              disabled={!editing}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">
              <FaEnvelope /> Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              disabled={!editing}
              required
            />
          </div>

          {editing && (
            <>
              <div className="form-group">
                <label htmlFor="currentPassword">
                  <FaKey /> Senha Atual
                </label>
                <input
                  type="password"
                  id="currentPassword"
                  name="currentPassword"
                  value={formData.currentPassword}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="newPassword">
                  <FaKey /> Nova Senha
                </label>
                <input
                  type="password"
                  id="newPassword"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">
                  <FaKey /> Confirmar Nova Senha
                </label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                />
              </div>
            </>
          )}

          {editing ? (
            <div className="button-group">
              <button
                type="submit"
                className="submit-button"
                disabled={loading}
              >
                {loading ? 'Salvando...' : 'Salvar Alterações'}
              </button>
              <button
                type="button"
                className="cancel-button"
                onClick={() => setEditing(false)}
              >
                Cancelar
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="edit-button"
              onClick={() => setEditing(true)}
            >
              Editar Perfil
            </button>
          )}
        </form>
      </div>
    </div>
  );
};

export default Profile;
