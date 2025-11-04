/**
 * Protected Route Component
 * Requires authentication to access
 */
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'

interface ProtectedRouteProps {
  redirectTo?: string
  children?: React.ReactNode
}

export function ProtectedRoute({ redirectTo = '/login', children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuthStore()

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  // Render children or outlet for nested routes
  return children ? <>{children}</> : <Outlet />
}
