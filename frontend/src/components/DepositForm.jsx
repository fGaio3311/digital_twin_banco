// src/components/DepositForm.jsx
import React, { useState } from 'react'
import { deposit }  from '../api'

export default function DepositForm() {
  const [amount, setAmount]   = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const newBalance = await deposit(Number(amount))
      setSuccess(`Depósito realizado! Novo saldo: ${newBalance}`)
      setAmount('')
      setError('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao fazer depósito')
      setSuccess('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-sm mx-auto">
      <h2 className="text-xl mb-4">Depósito</h2>
      <div className="mb-4">
        <input
          type="number"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          placeholder="Valor"
          className="w-full p-2 border rounded"
          required
        />
      </div>
      <button
        type="submit"
        className="w-full bg-blue-500 text-white p-2 rounded"
      >
        Depositar
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      {success && <p className="text-green-500 mt-2">{success}</p>}
    </form>
  )
}
