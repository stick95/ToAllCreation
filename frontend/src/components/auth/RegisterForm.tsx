/**
 * Registration Form Component
 */
import { useState, type FormEvent } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { Link } from 'react-router-dom'
import logo from '../../assets/img/taclogo.png'

export function RegisterForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showVerification, setShowVerification] = useState(false)
  const [verificationCode, setVerificationCode] = useState('')
  const [passwordError, setPasswordError] = useState('')

  const { signUp, confirmSignUp, isLoading, error, clearError } = useAuthStore()

  const validatePassword = (pass: string): boolean => {
    // AWS Cognito password requirements
    if (pass.length < 8) {
      setPasswordError('Password must be at least 8 characters')
      return false
    }
    if (!/[A-Z]/.test(pass)) {
      setPasswordError('Password must contain at least one uppercase letter')
      return false
    }
    if (!/[a-z]/.test(pass)) {
      setPasswordError('Password must contain at least one lowercase letter')
      return false
    }
    if (!/[0-9]/.test(pass)) {
      setPasswordError('Password must contain at least one number')
      return false
    }
    if (!/[^A-Za-z0-9]/.test(pass)) {
      setPasswordError('Password must contain at least one special character')
      return false
    }
    setPasswordError('')
    return true
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    clearError()

    // Validate passwords match
    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match')
      return
    }

    // Validate password strength
    if (!validatePassword(password)) {
      return
    }

    try {
      await signUp(email, password)
      setShowVerification(true)
    } catch (error) {
      console.error('Registration failed:', error)
    }
  }

  const handleVerification = async (e: FormEvent) => {
    e.preventDefault()
    clearError()

    try {
      await confirmSignUp(email, verificationCode)
      // Redirect to login after successful verification
      window.location.href = '/login?verified=true'
    } catch (error) {
      console.error('Verification failed:', error)
    }
  }

  if (showVerification) {
    return (
      <div className="auth-form-container">
        <div className="auth-form">
          <img src={logo} alt="ToAllCreation Logo" className="auth-logo" />
          <h2>Verify Email</h2>
          <p className="subtitle">
            We sent a verification code to <strong>{email}</strong>
          </p>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleVerification}>
            <div className="form-group">
              <label htmlFor="code">Verification Code</label>
              <input
                id="code"
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                placeholder="Enter 6-digit code"
                required
                disabled={isLoading}
                maxLength={6}
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>

          <div className="form-footer">
            <p>
              Didn't receive code?{' '}
              <button
                className="link-button"
                onClick={() => handleSubmit(new Event('submit') as any)}
              >
                Resend
              </button>
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <img src={logo} alt="ToAllCreation Logo" className="auth-logo" />
        <h2>Create Account</h2>
        <p className="subtitle">Join ToAllCreation to start sharing</p>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {passwordError && (
          <div className="error-message">
            {passwordError}
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
              onChange={(e) => {
                setPassword(e.target.value)
                if (e.target.value) validatePassword(e.target.value)
              }}
              placeholder="Create a strong password"
              required
              disabled={isLoading}
              minLength={8}
            />
            <small className="form-hint">
              Must be 8+ characters with uppercase, lowercase, number, and special character
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
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
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="form-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
