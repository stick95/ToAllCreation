/**
 * Dashboard Page
 * Main posting interface for creating and publishing reels across platforms
 */
import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { DashboardLayout } from '../components/DashboardLayout'
import apiClient from '../lib/apiClient'
import '../styles/dashboard.css'

interface ConnectedAccount {
  account_id: string
  platform: string
  page_name?: string
  username?: string
  account_type?: string
}

export function Dashboard() {
  const navigate = useNavigate()
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [posting, setPosting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Post form state
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [caption, setCaption] = useState('')
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([])
  const [videoPreview, setVideoPreview] = useState<string | null>(null)

  // Load connected accounts
  useEffect(() => {
    loadAccounts()
  }, [])

  // Select all accounts by default when loaded
  useEffect(() => {
    if (accounts.length > 0 && selectedAccounts.length === 0) {
      setSelectedAccounts(accounts.map(account => account.account_id))
    }
  }, [accounts])

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

  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate video file
      if (!file.type.startsWith('video/')) {
        setError('Please select a valid video file')
        return
      }

      // Check file size (100MB limit)
      if (file.size > 100 * 1024 * 1024) {
        setError('Video file must be less than 100MB')
        return
      }

      setVideoFile(file)
      setError(null)

      // Create preview URL
      const previewUrl = URL.createObjectURL(file)
      setVideoPreview(previewUrl)
    }
  }

  const toggleAccountSelection = (accountId: string) => {
    setSelectedAccounts(prev =>
      prev.includes(accountId)
        ? prev.filter(id => id !== accountId)
        : [...prev, accountId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedAccounts.length === accounts.length) {
      // Deselect all
      setSelectedAccounts([])
    } else {
      // Select all
      setSelectedAccounts(accounts.map(account => account.account_id))
    }
  }

  const allSelected = accounts.length > 0 && selectedAccounts.length === accounts.length

  const handlePost = async () => {
    if (!videoFile) {
      setError('Please select a video to post')
      return
    }

    if (selectedAccounts.length === 0) {
      setError('Please select at least one account to post to')
      return
    }

    try {
      setPosting(true)
      setError(null)
      setSuccess(null)

      // Step 1: Get presigned S3 upload URL
      const uploadUrlResponse = await apiClient.post('/api/social/upload-url', {
        filename: videoFile.name,
        content_type: videoFile.type
      })

      const { upload_url, s3_key } = uploadUrlResponse.data

      // Step 2: Upload video directly to S3
      const uploadResponse = await fetch(upload_url, {
        method: 'PUT',
        body: videoFile,
        headers: {
          'Content-Type': videoFile.type
        }
      })

      if (!uploadResponse.ok) {
        throw new Error(`S3 upload failed: ${uploadResponse.statusText}`)
      }

      // Step 3: Create async upload request
      await apiClient.post('/api/social/post', {
        s3_key: s3_key,
        caption: caption,
        account_ids: selectedAccounts
      })

      // Redirect to uploads page to see status
      navigate('/uploads')

    } catch (err: any) {
      console.error('Error posting:', err)
      setError(err.response?.data?.detail || 'Failed to post. Please try again.')
    } finally {
      setPosting(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout title="Create & Post Reel" subtitle="Share your message across all platforms">
        <div className="dashboard-loading">Loading...</div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Create & Post Reel" subtitle="Share your message across all platforms">
      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="post-composer">
        {/* Video Upload Section */}
        <div className="composer-section">
          <h3>Upload Video</h3>
          <div className="video-upload-area">
            {videoPreview ? (
              <div className="video-preview">
                <video src={videoPreview} controls className="preview-video" />
                <button
                  className="btn-remove-video"
                  onClick={() => {
                    setVideoFile(null)
                    setVideoPreview(null)
                  }}
                >
                  × Remove Video
                </button>
              </div>
            ) : (
              <label className="upload-label">
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleVideoSelect}
                  className="upload-input"
                />
                <div className="upload-placeholder">
                  <span className="upload-icon">📹</span>
                  <p>Click to upload video</p>
                  <span className="upload-hint">Max 100MB</span>
                </div>
              </label>
            )}
          </div>
        </div>

        {/* Caption Section */}
        <div className="composer-section">
          <h3>Caption</h3>
          <textarea
            className="caption-input"
            placeholder="Write your caption here..."
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            rows={4}
          />
          <span className="caption-count">{caption.length} characters</span>
        </div>

        {/* Account Selection */}
        <div className="composer-section">
          <h3>Post To</h3>
          {accounts.length === 0 ? (
            <div className="no-accounts">
              <p>No accounts connected yet.</p>
              <Link to="/accounts">
                <button className="btn btn-secondary">Connect Accounts</button>
              </Link>
            </div>
          ) : (
            <div className="accounts-list">
              {/* Select All Checkbox */}
              <label className="account-checkbox select-all">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleSelectAll}
                />
                <div className="account-info">
                  <span className="account-platform" style={{ fontWeight: 'bold' }}>Select All</span>
                  <span className="account-name">
                    {selectedAccounts.length} of {accounts.length} selected
                  </span>
                </div>
              </label>

              {/* Individual Account Checkboxes */}
              {accounts.map(account => (
                <label key={account.account_id} className="account-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedAccounts.includes(account.account_id)}
                    onChange={() => toggleAccountSelection(account.account_id)}
                  />
                  <div className="account-info">
                    <span className="account-platform">{account.platform}</span>
                    <span className="account-name">
                      {account.page_name || account.username || 'Personal Account'}
                    </span>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Post Button */}
        <div className="composer-actions">
          <button
            className="btn btn-primary btn-post"
            onClick={handlePost}
            disabled={posting || !videoFile || selectedAccounts.length === 0}
          >
            {posting ? 'Posting...' : `Post to ${selectedAccounts.length} Account${selectedAccounts.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </DashboardLayout>
  )
}
