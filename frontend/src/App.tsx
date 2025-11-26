import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { LoginForm } from './components/auth/LoginForm'
import { RegisterForm } from './components/auth/RegisterForm'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { Accounts } from './pages/Accounts'
import { Dashboard } from './pages/Dashboard'
import { Uploads } from './pages/Uploads'
import { Privacy } from './pages/Privacy'
import { Terms } from './pages/Terms'
import logo from './assets/img/taclogo.png'
import './App.css'

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
        <p>He said to them, “Go into all the world and preach the gospel to all creation."</p>

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
        <Route
          path="/accounts"
          element={
            <ProtectedRoute>
              <Accounts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/uploads"
          element={
            <ProtectedRoute>
              <Uploads />
            </ProtectedRoute>
          }
        />
        <Route
          path="/privacy"
          element={
            <ProtectedRoute>
              <Privacy />
            </ProtectedRoute>
          }
        />
        <Route
          path="/terms"
          element={
            <ProtectedRoute>
              <Terms />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
