/**
 * Reset Password Form Component
 */
import { useState, type FormEvent } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import logo from '../../assets/img/taclogo.png'

export function ResetPasswordForm() {
  const location = useLocation()
  const navigate = useNavigate()
  const [email, setEmail] = useState(location.state?.email || '')
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmNewPassword, setConfirmNewPassword] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)
  const { confirmPassword, isLoading, error, clearError } = useAuthStore()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    clearError()
    setLocalError(null)

    // Validate passwords match
    if (newPassword !== confirmNewPassword) {
      setLocalError('Passwords do not match')
      return
    }

    // Validate password length
    if (newPassword.length < 8) {
      setLocalError('Password must be at least 8 characters')
      return
    }

    try {
      await confirmPassword(email, code, newPassword)
      // Success! Navigate to login
      navigate('/login', {
        state: { message: 'Password reset successful! Please sign in with your new password.' }
      })
    } catch (error) {
      console.error('Password reset failed:', error)
    }
  }

  const displayError = error || localError

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <img src={logo} alt="ToAllCreation Logo" className="auth-logo" />
        <h2>Reset Password</h2>
        <p className="subtitle">Enter the code from your email and choose a new password.</p>

        {displayError && (
          <div className="error-message">
            {displayError}
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
            <label htmlFor="code">Reset Code</label>
            <input
              id="code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter code from email"
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <input
              id="newPassword"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password"
              required
              disabled={isLoading}
              minLength={8}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmNewPassword">Confirm New Password</label>
            <input
              id="confirmNewPassword"
              type="password"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              placeholder="Confirm new password"
              required
              disabled={isLoading}
              minLength={8}
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        <div className="form-footer">
          <p>
            Remember your password?{' '}
            <Link to="/login">Sign in</Link>
          </p>
          <p>
            Need a new code?{' '}
            <Link to="/forgot-password">Resend code</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
