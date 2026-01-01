// src/App.js
import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LoginForm from './components/LoginForm'
import Dashboard from './components/Dashboard'
import Admin from './pages/Admin'

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const username = localStorage.getItem('username')

  if (!token) {
    return <LoginForm onLogin={(t, u) => {
      setToken(t)
      localStorage.setItem('username', u)
    }} />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admin" element={username === 'admin' ? <Admin /> : <Dashboard />} />
        <Route path="/" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
