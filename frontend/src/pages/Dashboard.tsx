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

  // Scheduling state
  const [isScheduled, setIsScheduled] = useState(false)
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('')

  // TikTok-specific settings
  const [tiktokPrivacy, setTiktokPrivacy] = useState('')  // No default value per TikTok requirements
  const [tiktokAllowComments, setTiktokAllowComments] = useState(true)
  const [tiktokAllowDuet, setTiktokAllowDuet] = useState(false)
  const [tiktokAllowStitch, setTiktokAllowStitch] = useState(false)
  const [tiktokCommercialContent, setTiktokCommercialContent] = useState(false)
  const [tiktokCommercialType, setTiktokCommercialType] = useState('')  // 'your_brand' or 'branded_content'
  const [tiktokAgreement, setTiktokAgreement] = useState(false)

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

  // Cleanup video preview URL to prevent memory leaks
  useEffect(() => {
    return () => {
      if (videoPreview) {
        URL.revokeObjectURL(videoPreview)
      }
    }
  }, [videoPreview])

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

  // Check if TikTok account is selected
  const hasTikTokSelected = selectedAccounts.some(accountId => {
    const account = accounts.find(acc => acc.account_id === accountId)
    return account?.platform.toLowerCase() === 'tiktok'
  })

  const handlePost = async () => {
    if (!videoFile) {
      setError('Please select a video to post')
      return
    }

    if (selectedAccounts.length === 0) {
      setError('Please select at least one account to post to')
      return
    }

    // Validate TikTok-specific requirements
    if (hasTikTokSelected) {
      if (!tiktokPrivacy) {
        setError('Please select a privacy level for TikTok')
        return
      }
      if (!tiktokAgreement) {
        setError('Please agree to TikTok\'s Music Usage Confirmation')
        return
      }
      if (tiktokCommercialContent && !tiktokCommercialType) {
        setError('Please select commercial content type for TikTok')
        return
      }
      // Disable private option if branded content is selected
      if (tiktokCommercialType === 'branded_content' && tiktokPrivacy === 'PRIVATE_TO_SELF') {
        setError('Branded content visibility cannot be set to private on TikTok')
        return
      }
    }

    // Validate scheduling if enabled
    if (isScheduled) {
      if (!scheduledDate || !scheduledTime) {
        setError('Please select both date and time for scheduled post')
        return
      }

      // Convert to Unix timestamp and validate it's at least 1 hour in the future
      const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`)
      const now = new Date()
      const oneHourFromNow = new Date(now.getTime() + (60 * 60 * 1000))

      if (scheduledDateTime <= now) {
        setError('Scheduled time must be in the future')
        return
      }

      if (scheduledDateTime < oneHourFromNow) {
        setError('Posts must be scheduled at least 1 hour in advance. For immediate posting, uncheck "Schedule Post"')
        return
      }
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

      // Step 3: Create scheduled post or immediate post
      if (isScheduled) {
        // Calculate Unix timestamp for scheduled time
        const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`)
        const scheduledTimestamp = Math.floor(scheduledDateTime.getTime() / 1000)

        // Get the video URL from S3
        const videoUrl = `https://toallcreation-video-uploads.s3.amazonaws.com/${s3_key}`

        // Create scheduled post
        const scheduledPostData: any = {
          video_url: videoUrl,
          caption: caption,
          destinations: selectedAccounts,
          scheduled_time: scheduledTimestamp,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }

        // Add TikTok settings if TikTok is selected
        if (hasTikTokSelected) {
          scheduledPostData.tiktok_settings = {
            privacy_level: tiktokPrivacy,
            disable_comment: !tiktokAllowComments,
            disable_duet: !tiktokAllowDuet,
            disable_stitch: !tiktokAllowStitch,
            commercial_content: tiktokCommercialContent,
            commercial_type: tiktokCommercialType || undefined
          }
        }

        await apiClient.post('/api/scheduled-posts', scheduledPostData)

        // Redirect to scheduled posts page to see the scheduled post
        navigate('/scheduled')
      } else {
        // Create immediate upload request
        const postData: any = {
          s3_key: s3_key,
          caption: caption,
          account_ids: selectedAccounts
        }

        // Add TikTok settings if TikTok is selected
        if (hasTikTokSelected) {
          postData.tiktok_settings = {
            privacy_level: tiktokPrivacy,
            disable_comment: !tiktokAllowComments,
            disable_duet: !tiktokAllowDuet,
            disable_stitch: !tiktokAllowStitch,
            commercial_content: tiktokCommercialContent,
            commercial_type: tiktokCommercialType || undefined
          }
        }

        await apiClient.post('/api/social/post', postData)

        // Redirect to uploads page to see status
        navigate('/uploads')
      }

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
                    if (videoPreview) {
                      URL.revokeObjectURL(videoPreview)
                    }
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
              {accounts.map(account => {
                const isTikTok = account.platform.toLowerCase() === 'tiktok'
                const isTikTokSelected = selectedAccounts.includes(account.account_id) && isTikTok

                return (
                  <div
                    key={account.account_id}
                    style={isTikTok ? {
                      padding: 'var(--spacing-md)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--gray-300)',
                      backgroundColor: 'white'
                    } : {}}
                  >
                    <label className="account-checkbox">
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

                      {/* TikTok Settings - shown when TikTok account is selected */}
                      {isTikTokSelected && (
                      <div style={{
                        marginTop: '0.75rem',
                        fontSize: '0.875rem',
                        padding: 'var(--spacing-md)',
                        backgroundColor: 'var(--gray-50)',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--gray-200)'
                      }}>
                        {/* Privacy Level */}
                        <div style={{ marginBottom: '0.75rem' }}>
                          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: '600' }}>
                            Privacy <span style={{ color: 'red' }}>*</span>
                          </label>
                          <select
                            value={tiktokPrivacy}
                            onChange={(e) => setTiktokPrivacy(e.target.value)}
                            style={{
                              width: '100%',
                              padding: '0.5rem',
                              border: '1px solid var(--gray-300)',
                              borderRadius: '6px',
                              fontSize: '0.875rem'
                            }}
                          >
                            <option value="">Select...</option>
                            <option value="PUBLIC_TO_EVERYONE">Public</option>
                            <option value="MUTUAL_FOLLOW_FRIENDS">Friends</option>
                            <option value="SELF_ONLY" disabled={tiktokCommercialType === 'branded_content'}>
                              Private {tiktokCommercialType === 'branded_content' ? '(N/A for branded)' : ''}
                            </option>
                          </select>
                        </div>

                        {/* Interaction Settings - All in one row */}
                        <div style={{ marginBottom: '0.75rem' }}>
                          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: '600' }}>Allow</label>
                          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer' }}>
                              <input
                                type="checkbox"
                                checked={tiktokAllowComments}
                                onChange={(e) => setTiktokAllowComments(e.target.checked)}
                              />
                              <span>Comments</span>
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer' }}>
                              <input
                                type="checkbox"
                                checked={tiktokAllowDuet}
                                onChange={(e) => setTiktokAllowDuet(e.target.checked)}
                              />
                              <span>Duet</span>
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer' }}>
                              <input
                                type="checkbox"
                                checked={tiktokAllowStitch}
                                onChange={(e) => setTiktokAllowStitch(e.target.checked)}
                              />
                              <span>Stitch</span>
                            </label>
                          </div>
                        </div>

                        {/* Commercial Content - Row Layout */}
                        <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                            <input
                              type="checkbox"
                              checked={tiktokCommercialContent}
                              onChange={(e) => {
                                setTiktokCommercialContent(e.target.checked)
                                if (!e.target.checked) setTiktokCommercialType('')
                              }}
                            />
                            <span style={{ fontWeight: '600' }}>Commercial Content</span>
                          </label>

                          {tiktokCommercialContent && (
                            <select
                              value={tiktokCommercialType}
                              onChange={(e) => {
                                setTiktokCommercialType(e.target.value)
                                if (e.target.value === 'branded_content' && tiktokPrivacy === 'SELF_ONLY') {
                                  setTiktokPrivacy('')
                                }
                              }}
                              style={{
                                flex: 1,
                                padding: '0.5rem',
                                border: '1px solid var(--gray-300)',
                                borderRadius: '6px',
                                fontSize: '0.875rem'
                              }}
                            >
                              <option value="">Type...</option>
                              <option value="your_brand">Your Brand</option>
                              <option value="branded_content">Branded (Paid)</option>
                            </select>
                          )}
                        </div>

                        {/* Legal Agreement - Aligned with checkboxes */}
                        <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                            <input
                              type="checkbox"
                              checked={tiktokAgreement}
                              onChange={(e) => setTiktokAgreement(e.target.checked)}
                            />
                            <span>
                              Agree to{' '}
                              <a
                                href="https://www.tiktok.com/legal/music-usage-confirmation"
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ color: 'var(--blue-600)', textDecoration: 'underline' }}
                              >
                                Music Usage
                              </a>
                              {tiktokCommercialType === 'branded_content' && (
                                <> &{' '}
                                  <a
                                    href="https://www.tiktok.com/legal/page/row/bc-policy/en"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ color: 'var(--blue-600)', textDecoration: 'underline' }}
                                  >
                                    Branded Policy
                                  </a>
                                </>
                              )}
                            </span>
                          </label>
                        </div>
                      </div>
                      )}
                    </label>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Scheduling Section */}
        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--gray-300, #e5e7eb)' }} />
        <div className="composer-section">
          <label className="account-checkbox">
            <input
              type="checkbox"
              checked={isScheduled}
              onChange={(e) => setIsScheduled(e.target.checked)}
            />
            <div className="account-info">
              <span className="account-platform" style={{ fontWeight: 'bold' }}>Schedule Post</span>
              <span className="account-name">Post at a specific date and time</span>
            </div>
          </label>

          {isScheduled && (
            <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ flex: '1', minWidth: '200px' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: 'var(--gray-700)' }}>
                  Date
                </label>
                <input
                  type="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  className="caption-input"
                  style={{ padding: '0.75rem' }}
                  required={isScheduled}
                />
              </div>
              <div style={{ flex: '1', minWidth: '200px' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: 'var(--gray-700)' }}>
                  Time
                </label>
                <input
                  type="time"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="caption-input"
                  style={{ padding: '0.75rem' }}
                  required={isScheduled}
                />
              </div>
            </div>
          )}
        </div>

        {/* Scheduling Info */}
        {isScheduled && (
          <div style={{
            padding: '0.75rem 1rem',
            marginTop: '1rem',
            backgroundColor: 'var(--blue-50, #eff6ff)',
            border: '1px solid var(--blue-200, #bfdbfe)',
            borderRadius: '8px',
            color: 'var(--blue-700, #1d4ed8)',
            fontSize: '0.875rem'
          }}>
            Posts must be scheduled at least 1 hour in advance. For immediate posting, uncheck "Schedule Post".
          </div>
        )}

        {/* Post Button */}
        <div className="composer-actions">
          <button
            className="btn btn-primary btn-post"
            onClick={handlePost}
            disabled={posting || !videoFile || selectedAccounts.length === 0}
          >
            {posting
              ? (isScheduled ? 'Scheduling...' : 'Posting...')
              : (isScheduled
                  ? `Schedule for ${selectedAccounts.length} Account${selectedAccounts.length !== 1 ? 's' : ''}`
                  : `Post to ${selectedAccounts.length} Account${selectedAccounts.length !== 1 ? 's' : ''}`
                )
            }
          </button>
        </div>
      </div>
    </DashboardLayout>
  )
}
