import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { LoginForm } from './components/auth/LoginForm'
import { RegisterForm } from './components/auth/RegisterForm'
import { ForgotPasswordForm } from './components/auth/ForgotPasswordForm'
import { ResetPasswordForm } from './components/auth/ResetPasswordForm'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { LandingPage } from './pages/LandingPage'
import { Accounts } from './pages/Accounts'
import { CreateReel } from './pages/CreateReel'
import { Uploads } from './pages/Uploads'
import { ScheduledPosts } from './pages/ScheduledPosts'
import { Privacy } from './pages/Privacy'
import { Terms } from './pages/Terms'
import './App.css'

// Home route - redirect authenticated users to create-reel, otherwise show landing page
function Home() {
  const { isAuthenticated } = useAuthStore()

  if (isAuthenticated) {
    return <Navigate to="/create-reel" replace />
  }

  return <LandingPage />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/home" element={<LandingPage />} />
        <Route path="/login" element={<LoginForm />} />
        <Route path="/register" element={<RegisterForm />} />
        <Route path="/forgot-password" element={<ForgotPasswordForm />} />
        <Route path="/reset-password" element={<ResetPasswordForm />} />
        <Route
          path="/create-reel"
          element={
            <ProtectedRoute>
              <CreateReel />
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
          path="/scheduled"
          element={
            <ProtectedRoute>
              <ScheduledPosts />
            </ProtectedRoute>
          }
        />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
