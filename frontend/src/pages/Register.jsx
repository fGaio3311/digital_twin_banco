// src/pages/Register.jsx
import React from "react";
import LoginForm from "../components/LoginForm";

export default function Register() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-6 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-4 text-center">Registro</h1>
        <LoginForm isRegister />
      </div>
    </div>
  );
}
