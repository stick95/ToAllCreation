import { useState } from 'react'
import './App.css'

function App() {
  const [apiResponse, setApiResponse] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Update this URL after deploying to AWS
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000'

  const testBackend = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/hello`)
      const data = await response.json()
      setApiResponse(data)
    } catch (err) {
      setError('Failed to connect to backend. Make sure the backend is running.')
      console.error('API Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>ToAllCreation</h1>
        <p>Hello World - Frontend + Backend Test</p>

        <div className="card">
          <button onClick={testBackend} disabled={loading}>
            {loading ? 'Loading...' : 'Test Backend API'}
          </button>

          {error && (
            <div style={{ color: 'red', marginTop: '20px' }}>
              <p>❌ {error}</p>
            </div>
          )}

          {apiResponse && (
            <div style={{ marginTop: '20px', textAlign: 'left' }}>
              <h3>✅ Backend Response:</h3>
              <pre style={{
                background: '#1a1a1a',
                padding: '15px',
                borderRadius: '8px',
                overflow: 'auto'
              }}>
                {JSON.stringify(apiResponse, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div style={{ marginTop: '40px', fontSize: '14px', opacity: 0.7 }}>
          <p>Frontend: React + Vite + TypeScript</p>
          <p>Backend: FastAPI + AWS Lambda + SAM</p>
        </div>
      </header>
    </div>
  )
}

export default App
