import React from "react";
import DepositForm from "../components/DepositForm";

export default function DepositPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-6 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-4 text-center">Depósito</h1>
        <DepositForm />
      </div>
    </div>
  );
}
