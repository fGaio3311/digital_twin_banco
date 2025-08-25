import React, { useEffect, useState } from "react";
import { getLogs } from "../api/api";

export default function LogsPage() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    getLogs().then(setLogs);
  }, []);

  return (
    <div className="p-6 min-h-screen bg-gray-50">
      <h1 className="text-3xl font-semibold text-center mb-6">Logs</h1>
      <div className="overflow-x-auto">
        <table className="min-w-full table-auto border-collapse border border-gray-300">
          <thead className="bg-gray-200">
            <tr>
              <th className="border border-gray-300 p-2">Data</th>
              <th className="border border-gray-300 p-2">Usuário</th>
              <th className="border border-gray-300 p-2">Ação</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, i) => (
              <tr key={i}>
                <td className="border border-gray-300 p-2">{log.timestamp}</td>
                <td className="border border-gray-300 p-2">{log.user}</td>
                <td className="border border-gray-300 p-2">{log.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
