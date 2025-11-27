/**
 * Scheduled Posts Page
 * View and manage scheduled social media posts
 */
import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { DashboardLayout } from '../components/DashboardLayout'
import apiClient from '../lib/apiClient'
import { getPlatformIcon } from '../utils/platformIcons'
import '../styles/uploads.css'

interface ScheduledPost {
  scheduled_post_id: string
  user_id: string
  video_url: string
  caption: string
  destinations: string[]
  scheduled_time: number
  timezone: string
  status: 'scheduled' | 'processing' | 'posted' | 'cancelled' | 'failed'
  created_at: number
  updated_at: number
  request_id?: string
  error?: string
}

export function ScheduledPosts() {
  const [posts, setPosts] = useState<ScheduledPost[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [expandedVideos, setExpandedVideos] = useState<Set<string>>(new Set())

  // Load scheduled posts
  useEffect(() => {
    loadPosts()
  }, [])

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      loadPosts(true) // Silent refresh
    }, 30000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  const loadPosts = async (silent = false) => {
    try {
      if (!silent) setLoading(true)
      const response = await apiClient.get('/api/scheduled-posts?limit=50')
      setPosts(response.data.posts || [])
      setError(null)
    } catch (err: any) {
      console.error('Error loading scheduled posts:', err)
      if (!silent) setError(err.response?.data?.detail || 'Failed to load scheduled posts')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const cancelPost = async (scheduledPostId: string) => {
    if (!confirm('Are you sure you want to cancel this scheduled post?')) {
      return
    }

    try {
      await apiClient.delete(`/api/scheduled-posts/${scheduledPostId}`)
      await loadPosts()
      setError(null)
    } catch (err: any) {
      console.error('Error cancelling post:', err)
      setError(err.response?.data?.detail || 'Failed to cancel post')
    }
  }

  const formatDateTime = useCallback((timestamp: number, timezone?: string) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZone: timezone || undefined
    })
  }, [])

  const getTimeUntil = useCallback((timestamp: number) => {
    const now = Date.now() / 1000
    const diff = timestamp - now

    if (diff < 0) return 'Past due'

    const hours = Math.floor(diff / 3600)
    const minutes = Math.floor((diff % 3600) / 60)

    if (hours > 24) {
      const days = Math.floor(hours / 24)
      return `in ${days} day${days !== 1 ? 's' : ''}`
    } else if (hours > 0) {
      return `in ${hours}h ${minutes}m`
    } else {
      return `in ${minutes}m`
    }
  }, [])

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'scheduled':
        return 'status-queued'
      case 'processing':
        return 'status-processing'
      case 'posted':
        return 'status-completed'
      case 'cancelled':
      case 'failed':
        return 'status-failed'
      default:
        return 'status-queued'
    }
  }, [])

  const toggleVideoExpanded = useCallback((postId: string) => {
    setExpandedVideos(prev => {
      const newSet = new Set(prev)
      if (newSet.has(postId)) {
        newSet.delete(postId)
      } else {
        newSet.add(postId)
      }
      return newSet
    })
  }, [])

  // Filter to only show scheduled and processing posts (limit to next 8)
  const activePosts = posts
    .filter(p => p.status === 'scheduled' || p.status === 'processing')
    .slice(0, 8)

  if (loading) {
    return (
      <DashboardLayout title="Scheduled Posts" subtitle="Manage your scheduled social media posts">
        <div className="uploads-loading">Loading scheduled posts...</div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Scheduled Posts" subtitle="Manage your scheduled social media posts">
      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {posts.filter(p => p.status === 'scheduled' || p.status === 'processing').length > 8 && (
        <div style={{
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          backgroundColor: 'var(--blue-50, #eff6ff)',
          border: '1px solid var(--blue-200, #bfdbfe)',
          borderRadius: '8px',
          color: 'var(--blue-700, #1d4ed8)',
          fontSize: '0.875rem'
        }}>
          Showing next 8 scheduled posts. You have {posts.filter(p => p.status === 'scheduled' || p.status === 'processing').length} total scheduled posts.
        </div>
      )}

      {activePosts.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--gray-600)' }}>
          No scheduled posts.
        </div>
      ) : (
        <div className="uploads-list">
          {activePosts.map((post) => (
            <div key={post.scheduled_post_id} className="upload-card">
              <div className="upload-header">
                <div className="upload-info">
                  <h3 className="upload-title">
                    Scheduled for {formatDateTime(post.scheduled_time, post.timezone)}
                  </h3>
                  <p className="upload-subtitle">
                    {getTimeUntil(post.scheduled_time)} • {post.destinations.length} destination{post.destinations.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>

              <div className="upload-body">
                <div className="upload-video-preview" style={{ marginBottom: '1rem' }}>
                  <button
                    onClick={() => toggleVideoExpanded(post.scheduled_post_id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--blue-600, #2563eb)',
                      cursor: 'pointer',
                      padding: 0,
                      font: 'inherit'
                    }}
                  >
                    {expandedVideos.has(post.scheduled_post_id) ? 'Hide Video' : 'View Video'}
                  </button>
                </div>
                {expandedVideos.has(post.scheduled_post_id) && (
                  <div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
                    <video
                      src={post.video_url}
                      controls
                      style={{ width: '100%', maxHeight: '300px', borderRadius: '8px' }}
                    />
                  </div>
                )}

                {post.caption && (
                  <div className="upload-caption">
                    <strong>Caption:</strong>
                    <p style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>{post.caption}</p>
                  </div>
                )}

                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '1rem', marginBottom: '1rem' }}>
                  {post.destinations.map((dest, idx) => {
                    const [platform] = dest.split(':')
                    const icon = getPlatformIcon(platform)
                    return icon ? (
                      <img
                        key={idx}
                        src={icon}
                        alt={platform}
                        title={platform}
                        style={{
                          width: '32px',
                          height: '32px',
                          objectFit: 'contain'
                        }}
                      />
                    ) : null
                  })}
                </div>
              </div>

              <div className="upload-footer">
                <div className="upload-metadata" style={{ marginBottom: '0.75rem' }}>
                  <span>Created: {formatDateTime(post.created_at)}</span>
                  {post.timezone && <span style={{ marginLeft: '1rem' }}>Timezone: {post.timezone}</span>}
                </div>
                <div className="upload-actions">
                  {post.status === 'scheduled' && (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => cancelPost(post.scheduled_post_id)}
                    >
                      Cancel Post
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  )
}
