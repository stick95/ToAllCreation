/**
 * Account Management Page
 * Allows users to link/unlink their social media accounts
 */
import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { DashboardLayout } from '../components/DashboardLayout'
import apiClient from '../lib/apiClient'
import '../styles/accounts.css'

// Import platform icons
import facebookIcon from '../assets/icons/facebook.svg'
import instagramIcon from '../assets/icons/instagram.png'
import twitterIcon from '../assets/icons/twitter.svg'
import youtubeIcon from '../assets/icons/youtube.svg'
import linkedinIcon from '../assets/icons/linkedin.png'
import tiktokIcon from '../assets/icons/tiktok.svg'

interface SocialAccount {
  account_id: string
  platform: string
  username?: string
  account_type?: string  // 'personal', 'page', 'business'
  page_name?: string     // For Facebook Pages / LinkedIn Company Pages
  created_at: number
  is_active: boolean
}

interface AvailablePage {
  id: string
  name: string
  access_token?: string
  category?: string
}

const PLATFORMS = [
  {
    id: 'facebook',
    name: 'Facebook',
    icon: facebookIcon,
    description: 'Connect to post to Pages you manage'
  },
  {
    id: 'instagram',
    name: 'Instagram',
    icon: instagramIcon,
    description: 'Connect Business accounts linked to your Facebook Pages'
  },
  {
    id: 'twitter',
    name: 'X (Twitter)',
    icon: twitterIcon,
    description: 'Post to your personal account'
  },
  {
    id: 'youtube',
    name: 'YouTube',
    icon: youtubeIcon,
    description: 'Upload videos as YouTube Shorts'
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: linkedinIcon,
    description: 'Post to your profile or Company Pages you manage'
  },
  {
    id: 'tiktok',
    name: 'TikTok',
    icon: tiktokIcon,
    description: 'Upload short videos to your TikTok account'
  }
]

export function Accounts() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null)

  // Page selection modal state
  const [showPageSelectionModal, setShowPageSelectionModal] = useState(false)
  const [availablePages, setAvailablePages] = useState<AvailablePage[]>([])
  const [selectedPageIds, setSelectedPageIds] = useState<string[]>([])
  const [savingPages, setSavingPages] = useState(false)
  const [currentPlatform, setCurrentPlatform] = useState<string | null>(null)

  // Load connected accounts
  useEffect(() => {
    loadAccounts()
  }, [])

  // Check for OAuth callback with select_pages parameter
  useEffect(() => {
    const platform = searchParams.get('platform')
    const selectPages = searchParams.get('select_pages')

    if (platform && selectPages === 'true') {
      // Clear the query params
      setSearchParams({})

      // Open page selection modal
      openPageSelectionModal(platform)
    }
  }, [searchParams])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/social/accounts')
      setAccounts(response.data.accounts || [])
      setError(null)
    } catch (err: any) {
      console.error('Error loading accounts:', err)
      setError(err.response?.data?.detail || 'Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const connectAccount = async (platform: string) => {
    try {
      setConnectingPlatform(platform)
      setError(null)

      // Get OAuth authorization URL
      const response = await apiClient.get(`/api/social/connect/${platform}`)
      const { authorization_url } = response.data

      // Redirect to OAuth provider
      window.location.href = authorization_url
    } catch (err: any) {
      console.error('Error connecting account:', err)
      setError(err.response?.data?.detail || `Failed to connect ${platform}`)
      setConnectingPlatform(null)
    }
  }

  const disconnectAccount = async (accountId: string, platform: string) => {
    if (!confirm(`Are you sure you want to disconnect your ${platform} account?`)) {
      return
    }

    try {
      await apiClient.delete(`/api/social/accounts/${accountId}`)
      await loadAccounts() // Reload accounts
    } catch (err: any) {
      console.error('Error disconnecting account:', err)
      setError(err.response?.data?.detail || 'Failed to disconnect account')
    }
  }

  const openPageSelectionModal = async (platform: string) => {
    try {
      setCurrentPlatform(platform)
      setError(null)

      // Fetch available pages from backend
      const response = await apiClient.get(`/api/social/pages/${platform}`)
      const pages = response.data.pages || []

      setAvailablePages(pages)
      setSelectedPageIds([]) // Reset selection
      setShowPageSelectionModal(true)
    } catch (err: any) {
      console.error('Error fetching pages:', err)
      setError(err.response?.data?.detail || `Failed to fetch ${platform} pages`)
    }
  }

  const togglePageSelection = (pageId: string) => {
    setSelectedPageIds(prev =>
      prev.includes(pageId)
        ? prev.filter(id => id !== pageId)
        : [...prev, pageId]
    )
  }

  const saveSelectedPages = async () => {
    if (!currentPlatform || selectedPageIds.length === 0) {
      return
    }

    try {
      setSavingPages(true)
      setError(null)

      // Save each selected page
      await apiClient.post('/api/social/accounts', {
        platform: currentPlatform,
        page_ids: selectedPageIds
      })

      // Close modal and reload accounts
      setShowPageSelectionModal(false)
      await loadAccounts()
    } catch (err: any) {
      console.error('Error saving pages:', err)
      setError(err.response?.data?.detail || 'Failed to save selected pages')
    } finally {
      setSavingPages(false)
    }
  }

  const getConnectedAccounts = (platformId: string) => {
    return accounts.filter(acc => acc.platform === platformId)
  }

  if (loading) {
    return (
      <DashboardLayout title="Manage Social Accounts" subtitle="Connect your social media accounts to post across multiple platforms">
        <div className="accounts-loading">Loading accounts...</div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Manage Social Accounts" subtitle="Connect your social media accounts to post across multiple platforms">
      <div className="accounts-container">
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="accounts-grid">
        {PLATFORMS.map(platform => {
          const connectedAccounts = getConnectedAccounts(platform.id)
          const isConnecting = connectingPlatform === platform.id

          return (
            <div key={platform.id} className="account-card">
              <div className="account-card-header">
                <img src={platform.icon} alt={platform.name} className="account-icon" />
                <h3>{platform.name}</h3>
              </div>

              <p className="platform-description">{platform.description}</p>

              <div className="account-card-body">
                {/* Show all connected accounts for this platform */}
                {connectedAccounts.length > 0 && (
                  <div className="connected-accounts-list">
                    {connectedAccounts.map(account => (
                      <div key={account.account_id} className="connected-account-item">
                        <div className="account-info">
                          <span className="account-name">
                            {account.page_name || account.username || 'Personal Account'}
                          </span>
                        </div>
                        <button
                          className="btn-disconnect"
                          onClick={() => disconnectAccount(account.account_id, platform.name)}
                          title="Disconnect"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add more button */}
                <button
                  className="btn btn-primary"
                  onClick={() => connectAccount(platform.id)}
                  disabled={isConnecting}
                >
                  {isConnecting ? 'Connecting...' :
                   connectedAccounts.length > 0 ? '+ Add Another' : 'Connect'}
                </button>
              </div>
            </div>
          )
        })}
        </div>

        <div className="accounts-footer">
          <p className="text-muted">
            Your access tokens are securely stored and encrypted.
          </p>
        </div>
      </div>

      {/* Page Selection Modal */}
      {showPageSelectionModal && (
        <div className="modal-overlay" onClick={() => setShowPageSelectionModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Select {currentPlatform} Pages</h2>
              <button
                className="modal-close"
                onClick={() => setShowPageSelectionModal(false)}
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              {availablePages.length === 0 ? (
                <p className="text-muted">No pages available to connect.</p>
              ) : (
                <div className="pages-list">
                  {availablePages.map(page => (
                    <label key={page.id} className="page-item">
                      <input
                        type="checkbox"
                        checked={selectedPageIds.includes(page.id)}
                        onChange={() => togglePageSelection(page.id)}
                      />
                      <div className="page-info">
                        <span className="page-name">{page.name}</span>
                        {page.category && (
                          <span className="page-category">{page.category}</span>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowPageSelectionModal(false)}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={saveSelectedPages}
                disabled={savingPages || selectedPageIds.length === 0}
              >
                {savingPages ? 'Saving...' : `Save ${selectedPageIds.length} Page${selectedPageIds.length !== 1 ? 's' : ''}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
