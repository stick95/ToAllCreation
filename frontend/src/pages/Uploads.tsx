/**
 * Uploads Monitoring Page
 * View and monitor async upload requests with detailed logs
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { DashboardLayout } from '../components/DashboardLayout'
import apiClient from '../lib/apiClient'
import '../styles/uploads.css'

interface UploadDestination {
  status: 'queued' | 'processing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  logs: LogEntry[]
  error?: string
  result?: any
}

interface UploadRequest {
  request_id: string
  user_id: string
  video_url: string
  caption: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  destinations: Record<string, UploadDestination>
  created_at: number
  updated_at: number
}

interface LogEntry {
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  [key: string]: any
}

export function Uploads() {
  const [requests, setRequests] = useState<UploadRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [logsData, setLogsData] = useState<any>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Load upload requests
  useEffect(() => {
    loadRequests()
  }, [])

  // Auto-disable refresh when all requests are completed or failed
  useEffect(() => {
    if (requests.length === 0) return

    const allDone = requests.every(
      req => req.status === 'completed' || req.status === 'failed'
    )

    if (allDone && autoRefresh) {
      setAutoRefresh(false)
    }
  }, [requests])

  // Auto-refresh every 5 seconds if enabled and there are in-progress requests
  useEffect(() => {
    if (!autoRefresh) return

    const hasInProgress = requests.some(
      req => req.status === 'queued' || req.status === 'processing'
    )

    if (!hasInProgress) return

    const interval = setInterval(() => {
      loadRequests(true) // Silent refresh
    }, 5000)

    return () => clearInterval(interval)
  }, [autoRefresh, requests])

  const loadRequests = async (silent = false) => {
    try {
      if (!silent) setLoading(true)
      const response = await apiClient.get('/api/social/uploads?limit=5')
      setRequests(response.data.requests || [])
      setError(null)
    } catch (err: any) {
      console.error('Error loading upload requests:', err)
      if (!silent) setError(err.response?.data?.detail || 'Failed to load upload requests')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const loadRequestDetails = async (requestId: string) => {
    try {
      await apiClient.get(`/api/social/uploads/${requestId}`)
      // Details loaded but not currently used in UI
    } catch (err: any) {
      console.error('Error loading request details:', err)
      setError(err.response?.data?.detail || 'Failed to load request details')
    }
  }

  const loadLogs = async (requestId: string, destination?: string) => {
    try {
      const url = destination
        ? `/api/social/uploads/${requestId}/logs?destination=${encodeURIComponent(destination)}`
        : `/api/social/uploads/${requestId}/logs`
      const response = await apiClient.get(url)
      setLogsData(response.data)
      setShowLogsModal(true)
    } catch (err: any) {
      console.error('Error loading logs:', err)
      setError(err.response?.data?.detail || 'Failed to load logs')
    }
  }

  const resubmitTask = async (requestId: string, destination: string) => {
    try {
      await apiClient.post(`/api/social/uploads/${requestId}/resubmit`, {
        destination: destination
      })
      // Reload requests to show updated status
      await loadRequests()
      setError(null)
    } catch (err: any) {
      console.error('Error resubmitting task:', err)
      setError(err.response?.data?.detail || 'Failed to resubmit task')
    }
  }

  const copyLogsToClipboard = () => {
    if (!logsData) return
    const logsText = JSON.stringify(logsData, null, 2)
    navigator.clipboard.writeText(logsText)
    alert('Logs copied to clipboard!')
  }

  const downloadLogsAsJSON = () => {
    if (!logsData) return
    const logsText = JSON.stringify(logsData, null, 2)
    const blob = new Blob([logsText], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${logsData.request_id}-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'status-badge status-completed'
      case 'failed':
        return 'status-badge status-failed'
      case 'processing':
        return 'status-badge status-processing'
      case 'queued':
        return 'status-badge status-queued'
      default:
        return 'status-badge'
    }
  }

  const formatTimestamp = (timestamp: number | string) => {
    const date = typeof timestamp === 'number' ? new Date(timestamp * 1000) : new Date(timestamp)
    return date.toLocaleString()
  }

  const formatPlatform = (destination: string) => {
    const [platform] = destination.split(':')
    return platform.charAt(0).toUpperCase() + platform.slice(1)
  }

  // Check if all requests are done (completed or failed)
  const allRequestsDone = requests.length > 0 && requests.every(
    req => req.status === 'completed' || req.status === 'failed'
  )

  return (
    <DashboardLayout title="Upload Monitoring" subtitle="Track your posts across all platforms">
      <div className="uploads-container">
          {/* Controls */}
          <div className="uploads-controls">
            <button onClick={() => loadRequests()} disabled={loading} className="refresh-button">
              {loading ? 'Loading...' : 'Refresh'}
            </button>
            <label className="auto-refresh-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                disabled={allRequestsDone}
              />
              Auto-refresh (5s)
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading && requests.length === 0 && (
            <div className="loading-state">Loading upload requests...</div>
          )}

          {/* Empty State */}
          {!loading && requests.length === 0 && (
            <div className="empty-state">
              <p>No upload requests yet</p>
              <Link to="/dashboard">
                <button>Create Your First Post</button>
              </Link>
            </div>
          )}

          {/* Upload Requests List */}
          {requests.length > 0 && (
            <div className="uploads-list">
              {requests.map((request) => (
                <div key={request.request_id} className="upload-card">
                  <div className="upload-card-header">
                    <div className="upload-meta">
                      <span className="upload-timestamp">{formatTimestamp(request.created_at)}</span>
                      <span className={getStatusBadgeClass(request.status)}>{request.status}</span>
                    </div>
                    <button
                      className="view-details-button"
                      onClick={() => {
                        loadRequestDetails(request.request_id)
                      }}
                    >
                      View Details
                    </button>
                  </div>

                  <div className="upload-card-body">
                    {/* Video Thumbnail/Link */}
                    <div className="video-info">
                      <a href={request.video_url} target="_blank" rel="noopener noreferrer" className="video-link">
                        View Video
                      </a>
                    </div>

                    {/* Caption Preview */}
                    {request.caption && (
                      <div className="caption-preview">
                        {request.caption.length > 100
                          ? `${request.caption.substring(0, 100)}...`
                          : request.caption}
                      </div>
                    )}

                    {/* Destinations */}
                    <div className="destinations">
                      {Object.entries(request.destinations).map(([dest, destData]) => (
                        <div key={dest} className="destination-item">
                          <span className="destination-name">{formatPlatform(dest)}</span>
                          <span className={getStatusBadgeClass(destData.status)}>{destData.status}</span>
                          <div className="destination-actions">
                            <button
                              className="view-logs-button"
                              onClick={() => loadLogs(request.request_id, dest)}
                            >
                              View Logs
                            </button>
                            {destData.status === 'failed' && (
                              <button
                                className="resubmit-button"
                                onClick={() => resubmitTask(request.request_id, dest)}
                              >
                                Resubmit
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      {/* Logs Modal */}
      {showLogsModal && logsData && (
        <div className="modal-overlay" onClick={() => setShowLogsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Detailed Logs</h2>
              <button className="close-button" onClick={() => setShowLogsModal(false)}>×</button>
            </div>

            <div className="modal-body">
              {/* Log Actions */}
              <div className="log-actions">
                <button onClick={copyLogsToClipboard} className="action-button">
                  Copy to Clipboard
                </button>
                <button onClick={downloadLogsAsJSON} className="action-button">
                  Download JSON
                </button>
              </div>

              {/* Logs Display */}
              <div className="logs-container">
                {logsData.destination ? (
                  // Single destination logs
                  <>
                    <div className="log-meta">
                      <p><strong>Destination:</strong> {logsData.destination}</p>
                      <p><strong>Status:</strong> <span className={getStatusBadgeClass(logsData.status)}>{logsData.status}</span></p>
                      {logsData.error && (
                        <p className="error-text"><strong>Error:</strong> {logsData.error}</p>
                      )}
                    </div>
                    <div className="log-entries">
                      {logsData.logs && logsData.logs.length > 0 ? (
                        logsData.logs.map((log: LogEntry, index: number) => (
                          <div key={index} className={`log-entry log-${log.level.toLowerCase()}`}>
                            <span className="log-timestamp">{log.timestamp}</span>
                            <span className="log-level">{log.level}</span>
                            <span className="log-message">{log.message}</span>
                          </div>
                        ))
                      ) : (
                        <p>No logs available</p>
                      )}
                    </div>
                  </>
                ) : (
                  // All destinations logs
                  <>
                    <div className="log-meta">
                      <p><strong>Request ID:</strong> {logsData.request_id}</p>
                      <p><strong>Overall Status:</strong> <span className={getStatusBadgeClass(logsData.overall_status)}>{logsData.overall_status}</span></p>
                    </div>
                    {Object.entries(logsData.destinations).map(([dest, destData]: [string, any]) => (
                      <div key={dest} className="destination-logs">
                        <h3>{formatPlatform(dest)}</h3>
                        <p><strong>Status:</strong> <span className={getStatusBadgeClass(destData.status)}>{destData.status}</span></p>
                        {destData.error && (
                          <p className="error-text"><strong>Error:</strong> {destData.error}</p>
                        )}
                        <div className="log-entries">
                          {destData.logs && destData.logs.length > 0 ? (
                            destData.logs.map((log: LogEntry, index: number) => (
                              <div key={index} className={`log-entry log-${log.level.toLowerCase()}`}>
                                <span className="log-timestamp">{log.timestamp}</span>
                                <span className="log-level">{log.level}</span>
                                <span className="log-message">{log.message}</span>
                              </div>
                            ))
                          ) : (
                            <p>No logs available</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
