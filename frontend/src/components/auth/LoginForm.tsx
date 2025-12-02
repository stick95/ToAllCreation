/**
 * Login Form Component
 */
import { useState, type FormEvent } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import logo from '../../assets/img/taclogo.png'

export function LoginForm() {
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [successMessage] = useState(location.state?.message || null)
  const { signIn, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

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
    <div className="auth-form-container">
      <div className="auth-form">
        <img src={logo} alt="ToAllCreation Logo" className="auth-logo" />
        <h2>Sign In</h2>
        <p className="subtitle">Go into all the world and preach the gospel to all creation.</p>

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
  )
}
