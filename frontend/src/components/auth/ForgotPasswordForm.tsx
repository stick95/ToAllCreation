/**
 * Forgot Password Form Component
 */
import { useState, type FormEvent } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { Link, useNavigate } from 'react-router-dom'
import logo from '../../assets/img/taclogo.png'

export function ForgotPasswordForm() {
  const [email, setEmail] = useState('')
  const [success, setSuccess] = useState(false)
  const { forgotPassword, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    clearError()
    setSuccess(false)

    try {
      await forgotPassword(email)
      setSuccess(true)
    } catch (error) {
      console.error('Password reset request failed:', error)
    }
  }

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <img src={logo} alt="ToAllCreation Logo" className="auth-logo" />
        <h2>Reset Password</h2>
        <p className="subtitle">Enter your email to receive a password reset code.</p>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            Password reset code sent! Check your email and click the button below to reset your password.
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
              disabled={isLoading || success}
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading || success}
          >
            {isLoading ? 'Sending...' : 'Send Reset Code'}
          </button>
        </form>

        {success && (
          <div style={{ marginTop: '1rem' }}>
            <button
              className="btn btn-secondary"
              onClick={() => navigate('/reset-password', { state: { email } })}
              style={{ width: '100%' }}
            >
              I Have a Code
            </button>
          </div>
        )}

        <div className="form-footer">
          <p>
            Remember your password?{' '}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
