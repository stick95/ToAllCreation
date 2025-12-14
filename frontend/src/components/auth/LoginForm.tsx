/**
 * Login Form Component
 */
import { useState, type FormEvent } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import logo from '../../assets/img/taclogo.png'
import '../../styles/dashboard.css'

export function LoginForm() {
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [successMessage] = useState(location.state?.message || null)
  const { signIn, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    clearError()

    try {
      await signIn(email, password)
      navigate('/create-reel') // Redirect after successful login
    } catch (error) {
      // Error is handled by store
      console.error('Login failed:', error)
    }
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-top">
          <img src={logo} alt="ToAllCreation Logo" className="dashboard-logo" />
          <div className="menu-container">
            <button
              className="hamburger-btn"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Menu"
            >
              <span className="hamburger-line"></span>
              <span className="hamburger-line"></span>
              <span className="hamburger-line"></span>
            </button>
            {menuOpen && (
              <div className="dropdown-menu">
                <Link to="/home" className="menu-item">
                  Home
                </Link>
                <Link to="/login" className="menu-item">
                  Sign In
                </Link>
                <Link to="/register" className="menu-item">
                  Sign Up
                </Link>
                <div className="menu-divider"></div>
                <Link to="/privacy" className="menu-item menu-item-secondary">
                  Privacy
                </Link>
                <Link to="/terms" className="menu-item menu-item-secondary">
                  Terms
                </Link>
              </div>
            )}
          </div>
        </div>
        <h1>Sign In</h1>
        <p className="dashboard-subtitle">Go into all the world and preach the gospel to all creation.</p>
      </header>

      <div className="dashboard-content">
        <div className="auth-form-card">
          {successMessage && (
            <div className="alert alert-success">
              {successMessage}
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                disabled={isLoading}
                minLength={8}
              />
            </div>

            <div className="form-actions">
              <Link to="/forgot-password" className="link-secondary">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="form-footer">
            <p>
              Don't have an account?{' '}
              <Link to="/register">Sign up</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
