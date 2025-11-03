# ToAllCreation - Hello World

Simple full-stack Hello World application for testing CI/CD pipelines before building the full social media aggregator.

## What's Included

- **Backend**: FastAPI + AWS Lambda + SAM
- **Frontend**: React + Vite + TypeScript
- **CI/CD**: GitHub Actions workflows
- **Deployment**: AWS (Lambda + API Gateway + S3)

## Quick Start

### 1. Test Backend Locally

```bash
cd backend
sam build
sam local start-api --port 3000
```

Test: http://localhost:3000/api/hello

### 2. Test Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

Click "Test Backend API" to verify integration.

## Deploy to AWS

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.

Quick deploy:

```bash
# Backend
cd backend
sam build --use-container
sam deploy --guided

# Note the API URL from outputs, then update frontend/.env.local
# Frontend (manual for now)
cd frontend
npm run build
# Upload to S3 or serve via CloudFront
```

## Project Structure

```
ToAllCreation/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   └── __init__.py
│   ├── template.yaml        # SAM template
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main component
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
├── .github/
│   └── workflows/
│       ├── backend-deploy.yml
│       └── frontend-deploy.yml
└── docs/                    # Full project documentation
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/hello` - Test endpoint for frontend integration

## Environment Variables

### Backend
Set in AWS SAM template or Lambda console (none required for Hello World)

### Frontend
Create `frontend/.env.local`:
```
VITE_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com
```

## CI/CD

GitHub Actions workflows deploy automatically on push to `main`:

- Backend changes → `backend-deploy.yml` runs
- Frontend changes → `frontend-deploy.yml` runs

Required GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `VITE_API_URL`
- `S3_BUCKET` (for frontend)
- `CLOUDFRONT_DISTRIBUTION_ID` (optional)

## Testing

### Manual Tests

1. Backend health: `curl https://your-api.amazonaws.com/health`
2. Backend API: `curl https://your-api.amazonaws.com/api/hello`
3. Frontend: Visit your deployed frontend, click "Test Backend API"

### Expected Results

Backend response:
```json
{
  "message": "Hello from the backend!",
  "timestamp": "2025-11-03",
  "service": "ToAllCreation Backend API"
}
```

## Next Steps

Once Hello World is working:

1. Review full architecture in `docs/ARCHITECTURE.md`
2. Follow `docs/IMPLEMENTATION_CHECKLIST.md` for MVP features
3. Add authentication (Cognito)
4. Add database (DynamoDB)
5. Implement social media integrations

## Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- [docs/](./docs/) - Full project documentation
- [docs/QUICK_START.md](./docs/QUICK_START.md) - Full app quick start
- [docs/IMPLEMENTATION_CHECKLIST.md](./docs/IMPLEMENTATION_CHECKLIST.md) - Step-by-step implementation

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite
- **Backend**: Python 3.12, FastAPI, Mangum
- **Infrastructure**: AWS Lambda, API Gateway (HTTP API), SAM
- **CI/CD**: GitHub Actions

## License

Private project - All rights reserved
