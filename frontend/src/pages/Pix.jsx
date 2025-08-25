import React from "react";
import PixForm from "../components/PixForm";

export default function PixPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-6 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-4 text-center">Transferência PIX</h1>
        <PixForm />
      </div>
    </div>
  );
}
