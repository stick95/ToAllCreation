/**
 * Shared Dashboard Layout
 * Provides consistent header and navigation for dashboard pages
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import logo from '../assets/img/taclogo.png'
import '../styles/dashboard.css'

interface DashboardLayoutProps {
  children: React.ReactNode
  title: string
  subtitle?: string
}

export function DashboardLayout({ children, title, subtitle }: DashboardLayoutProps) {
  const { signOut } = useAuthStore()
  const [menuOpen, setMenuOpen] = useState(false)

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
                <Link to="/create-reel" className="menu-item">
                  Create Post
                </Link>
                <Link to="/accounts" className="menu-item">
                  Manage Accounts
                </Link>
                <Link to="/uploads" className="menu-item">
                  Upload History
                </Link>
                <Link to="/scheduled" className="menu-item">
                  Scheduled Posts
                </Link>
                <button onClick={() => signOut()} className="menu-item">
                  Sign Out
                </button>
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
        <h1>{title}</h1>
        {subtitle && <p className="dashboard-subtitle">{subtitle}</p>}
      </header>

      <div className="dashboard-content">
        {children}
      </div>
    </div>
  )
}
