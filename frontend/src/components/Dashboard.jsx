// src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react'
import { getBalance } from '../api'
import DepositForm from './DepositForm'
import PixForm from './PixForm'
import { useDigitalTwin } from '../hooks/useDigitalTwin'

export default function Dashboard() {
  const { balance, lastOperation } = useDigitalTwin()
  const [error, setError] = useState(null)

  const load = async () => {
    try {
      setError(null)
      await getBalance() // Removido setBalance
    } catch (err) {
      console.error('Erro ao carregar saldo:', err)
      if (err.response?.status === 401) {
        setError('Sessão expirada. Por favor, faça login novamente.')
      } else if (err.message.includes('CORS')) {
        setError('Erro de conexão com o servidor. CORS não configurado.')
      } else {
        setError('Não foi possível carregar saldo. Tente novamente.')
      }
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <strong>Erro:</strong> {error}
          <button
            onClick={load}
            className="ml-4 bg-red-500 text-white px-2 py-1 rounded"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    )
  }

  if (balance === null) {
    return (
      <div className="p-4">
        <div className="animate-pulse">Carregando saldo...</div>
      </div>
    )
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">Dashboard</h1>

      {/* Saldo */}
      <div className="bg-white p-4 rounded shadow mb-4">
        <h2 className="text-xl mb-2">Saldo atual</h2>
        <p className="text-3xl font-bold">
          {balance !== null ? `R$ ${balance}` : 'Carregando...'}
        </p>
      </div>

      {/* Última operação */}
      {lastOperation && (
        <div className="bg-gray-100 p-4 rounded mb-4">
          <h3 className="font-bold">Última operação</h3>
          <p>Tipo: {lastOperation.type}</p>
          <p>Valor: R$ {lastOperation.value}</p>
          <p>Data: {new Date(lastOperation.date).toLocaleString()}</p>
        </div>
      )}

      <DepositForm onDone={load} />
      <PixForm onDone={load} />
    </div>
  )
}
