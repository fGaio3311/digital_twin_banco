import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FaUser, FaSignOutAlt, FaExchangeAlt, FaChartLine } from 'react-icons/fa';
import './Layout.css';

const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <h2>Banco Digital</h2>
          <div className="user-info">
            <FaUser />
            <span>{user?.name}</span>
          </div>
        </div>

        <div className="sidebar-menu">
          <Link to="/dashboard" className="menu-item">
            <FaChartLine />
            <span>Dashboard</span>
          </Link>

          <Link to="/transfer" className="menu-item">
            <FaExchangeAlt />
            <span>Transferência</span>
          </Link>

          <Link to="/profile" className="menu-item">
            <FaUser />
            <span>Perfil</span>
          </Link>
        </div>

        <button onClick={handleLogout} className="logout-button">
          <FaSignOutAlt />
          <span>Sair</span>
        </button>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
