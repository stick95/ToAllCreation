import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { LoginForm } from './components/auth/LoginForm'
import { RegisterForm } from './components/auth/RegisterForm'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import logo from './assets/img/taclogo.png'
import './App.css'

// Dashboard component (protected)
function Dashboard() {
  const { user, signOut } = useAuthStore()

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} alt="ToAllCreation Logo" className="App-logo" />
        <h1>ToAllCreation - Dashboard</h1>
        <p>Welcome, {user?.email || user?.username}!</p>

        <div className="card">
          <h3>Your Profile</h3>
          <pre style={{
            background: '#1a1a1a',
            padding: '15px',
            borderRadius: '8px',
            overflow: 'auto',
            textAlign: 'left'
          }}>
            {JSON.stringify(user, null, 2)}
          </pre>

          <button
            onClick={() => signOut()}
            style={{ marginTop: '20px' }}
          >
            Sign Out
          </button>
        </div>
      </header>
    </div>
  )
}

// Public home page
function Home() {
  const { isAuthenticated } = useAuthStore()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} alt="ToAllCreation Logo" className="App-logo" />
        <h1>ToAllCreation</h1>
        <p>Welcome to ToAllCreation</p>

        <div className="card">
          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}>
            <Link to="/login">
              <button>Sign In</button>
            </Link>
            <Link to="/register">
              <button>Sign Up</button>
            </Link>
          </div>
        </div>

        <div style={{ marginTop: '40px', fontSize: '14px', opacity: 0.7 }}>
          <p>Frontend: React + Vite + TypeScript</p>
          <p>Backend: FastAPI + AWS Lambda + SAM</p>
          <p>Auth: AWS Cognito</p>
        </div>
      </header>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<LoginForm />} />
        <Route path="/register" element={<RegisterForm />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
