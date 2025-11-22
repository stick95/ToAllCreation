# Async Social Media Posting - Implementation Plan

## Overview
Transform the synchronous posting system into an async architecture with comprehensive logging.

## Current Progress

### ✅ Completed
1. **Infrastructure** (template.yaml):
   - DynamoDB table: `UploadRequestsTable` for tracking upload requests
   - SQS Queue: `PostingQueue` for async job processing
   - Dead Letter Queue: `PostingDeadLetterQueue` for failed jobs
   - Worker Lambda: `PostingWorkerFunction` to process SQS messages

2. **Backend Code**:
   - `posting_worker.py`: Async worker with DetailedLogger for comprehensive logging
   - `upload_requests.py`: Module for managing upload requests in DynamoDB

3. **Backend API Endpoints**:
   - ✅ Modified `POST /api/social/post` to use async pattern
   - ✅ Added `GET /api/social/uploads` - List all upload requests
   - ✅ Added `GET /api/social/uploads/{request_id}` - Get request details
   - ✅ Added `GET /api/social/uploads/{request_id}/logs` - Get detailed logs

4. **Deployment**:
   - ✅ Deployed infrastructure (DynamoDB, SQS, Worker Lambda)
   - ✅ Deployed updated API endpoints

### 🔧 Next Steps

#### 1. Create Frontend UI Page

**New page: `/uploads` or `/monitoring`**

Components needed:
- Upload requests list table with columns:
  - Timestamp
  - Video thumbnail/name
  - Destinations (with status badges)
  - Overall status
  - Actions (View Details, View Logs)

- Request details modal:
  - Video info
  - Caption
  - Destination-by-destination status
  - Links to detailed logs

- Logs viewer modal:
  - Filterable log entries (INFO/WARNING/ERROR)
  - Copy to clipboard button
  - Download as JSON button
  - Formatted display with timestamps

#### 2. Auto-refresh / Real-time Updates

Options:
- Polling every 5 seconds while requests are in progress
- WebSocket for real-time updates (future enhancement)

## Data Structure

### UploadRequest Record
```json
{
  "request_id": "uuid",
  "user_id": "user_id",
  "video_url": "https://...",
  "caption": "...",
  "created_at": 1234567890,
  "updated_at": 1234567890,
  "status": "queued|processing|completed|failed",
  "destinations": {
    "instagram:account_id_1": {
      "status": "queued|processing|completed|failed",
      "created_at": "ISO8601",
      "updated_at": "ISO8601",
      "logs": [
        {
          "timestamp": "ISO8601",
          "level": "INFO|WARNING|ERROR",
          "message": "...",
          ...additional fields
        }
      ],
      "error": "error message if failed",
      "result": {
        "media_id": "...",
        "post_id": "...",
        ...
      }
    },
    "facebook:page_id_1": {
      ...
    }
  },
  "ttl": 1234567890  // Auto-delete after 90 days
}
```

## Benefits

1. **No More Timeouts**: API returns immediately with request_id
2. **Comprehensive Logging**: Every step logged with timestamps
3. **Error Visibility**: Users can see exact error messages and copy/paste them
4. **Retry Capability**: Failed jobs automatically retry up to 3 times
5. **Scalability**: SQS queue can handle thousands of concurrent posts
6. **Future-Ready**: Easy to add scheduling (just delay the SQS message)

## Testing Plan

1. Test single destination post
2. Test multiple destinations post
3. Test error scenarios (invalid token, network error, etc.)
4. Verify logs are captured correctly
5. Test copy-to-clipboard functionality
6. Test auto-refresh in UI

## Deployment Steps

1. Deploy infrastructure (DynamoDB, SQS, Worker Lambda)
2. Deploy updated API endpoints
3. Deploy frontend UI changes
4. Monitor CloudWatch logs
5. Check DynamoDB records
6. Verify SQS queue metrics
