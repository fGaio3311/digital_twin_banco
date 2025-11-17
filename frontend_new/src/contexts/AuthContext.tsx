import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

interface User {
  id: number;
  username: string;
  balance: number;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshBalance: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUserProfile = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get(`${API_BASE_URL}/user/me`);
      setUser({
        id: response.data.id || 1,
        username: response.data.username,
        balance: response.data.balance,
      });
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, [fetchUserProfile]);

  const login = async (username: string, password: string) => {
    try {
      // Clear previous tokens
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      delete axios.defaults.headers.common['Authorization'];

      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      console.log('Attempting login with:', { username, password });

      const response = await axios.post(`${API_BASE_URL}/token`, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      console.log('Login response:', response.data);

      const { access_token } = response.data;

      if (!access_token) {
        throw new Error('Token não recebido do servidor');
      }

      localStorage.setItem('token', access_token);
      localStorage.setItem('username', username);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // Fetch user data
      const userResponse = await axios.get(`${API_BASE_URL}/user/me`);
      console.log('User response:', userResponse.data);

      setUser({
        id: userResponse.data.id,
        username: userResponse.data.username,
        balance: userResponse.data.balance,
      });
    } catch (error: any) {
      console.error('Login failed:', error);
      console.error('Error response:', error.response);

      // Clear any partial auth state
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      delete axios.defaults.headers.common['Authorization'];

      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      throw new Error(errorMessage);
    }
  };

  const register = async (username: string, password: string) => {
    try {
      await axios.post(`${API_BASE_URL}/register`, { username, password });
      await login(username, password);
    } catch (error: any) {
      console.error('Registration failed:', error);
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const refreshBalance = async () => {
    if (user) {
      try {
        const response = await axios.get(`${API_BASE_URL}/balance`);
        setUser(prev => prev ? { ...prev, balance: response.data.balance } : null);
      } catch (error) {
        console.error('Failed to refresh balance:', error);
      }
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    refreshBalance,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
