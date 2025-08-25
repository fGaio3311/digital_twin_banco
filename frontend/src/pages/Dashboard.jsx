import React from "react";
import Dashboard from "../components/Dashboard";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <h1 className="text-3xl font-semibold text-center mb-6">Dashboard</h1>
      <Dashboard />
    </div>
  );
}
