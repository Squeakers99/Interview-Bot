import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function BackendTest() {
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  async function testConnection() {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      console.error(err);
      setError(String(err));
    }
  }

  return (
    <div style={{ padding: 40 }}>
      <h1>Frontend ↔ Backend Test</h1>
      <button onClick={testConnection}>Test Backend Connection</button>

      {response && (
        <pre style={{ marginTop: 20 }}>
          {JSON.stringify(response, null, 2)}
        </pre>
      )}

      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
