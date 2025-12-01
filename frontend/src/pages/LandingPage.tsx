/**
 * Landing Page - Public marketing page for toallcreation.org
 */
import { Link } from 'react-router-dom'
import logo from '../assets/img/taclogo.png'
import '../styles/LandingPage.css'

export function LandingPage() {
  return (
    <div className="landing-page">
      {/* Navigation Header */}
      <header className="landing-header">
        <div className="container">
          <nav className="landing-nav">
            <div className="nav-brand">
              <img src={logo} alt="ToAllCreation" className="nav-logo" />
              <span className="nav-title">ToAllCreation</span>
            </div>
            <div className="nav-links">
              <Link to="/login" className="nav-link">Login</Link>
              <Link to="/register" className="nav-link-primary">Get Started</Link>
            </div>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="container">
          <div className="hero-content">
            <img src={logo} alt="ToAllCreation Logo" className="hero-logo" />
            <h1 className="hero-title">Go Into All The World</h1>
            <p className="hero-verse">
              "Go into all the world and preach the gospel to all creation." <br />
              <span className="verse-reference">- Mark 16:15</span>
            </p>
            <p className="hero-description">
              Share your message across all major social media platforms with a single click.
              Maximize your reach, minimize your effort.
            </p>
            <div className="hero-actions">
              <Link to="/register" className="btn-hero-primary">
                Start Free
              </Link>
              <Link to="/login" className="btn-hero-secondary">
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <h2 className="section-title">Spread Your Message Further</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🌐</div>
              <h3>Multi-Platform Posting</h3>
              <p>Post to Facebook, Instagram, Twitter, YouTube, LinkedIn, and TikTok simultaneously</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📅</div>
              <h3>Schedule Posts</h3>
              <p>Plan your content calendar and schedule posts for optimal engagement</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Instant Publishing</h3>
              <p>Share your content instantly across all platforms with one click</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Track Performance</h3>
              <p>Monitor post status and engagement across all platforms</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎥</div>
              <h3>Rich Media Support</h3>
              <p>Share images, videos, and text with full media support</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Secure & Private</h3>
              <p>Your credentials and content are protected with enterprise-grade security</p>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Support Section */}
      <section className="platforms-section">
        <div className="container">
          <h2 className="section-title">Supported Platforms</h2>
          <p className="section-subtitle">Connect once, post everywhere</p>
          <div className="platforms-grid">
            <div className="platform-badge">Facebook</div>
            <div className="platform-badge">Instagram</div>
            <div className="platform-badge">Twitter/X</div>
            <div className="platform-badge">YouTube</div>
            <div className="platform-badge">LinkedIn</div>
            <div className="platform-badge">TikTok</div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to Amplify Your Message?</h2>
            <p className="cta-description">
              Join content creators who are spreading the gospel to all creation
            </p>
            <Link to="/register" className="btn-cta">
              Get Started Free
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <img src={logo} alt="ToAllCreation" className="footer-logo" />
              <p className="footer-tagline">
                Empowering creators to share their message with the world
              </p>
            </div>
            <div className="footer-links">
              <div className="footer-section">
                <h4>Product</h4>
                <Link to="/login">Login</Link>
                <Link to="/register">Sign Up</Link>
              </div>
              <div className="footer-section">
                <h4>Legal</h4>
                <Link to="/privacy">Privacy Policy</Link>
                <Link to="/terms">Terms of Service</Link>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2025 ToAllCreation. All rights reserved.</p>
            <p className="footer-verse">
              "Therefore go and make disciples of all nations..." - Matthew 28:19
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
