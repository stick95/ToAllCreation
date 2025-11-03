# Unified Deployment Strategy

## Overview

The ToAllCreation project uses a **single unified deployment workflow** that deploys both backend and frontend together, ensuring version consistency and providing automatic rollback on failure.

## Why Unified Deployment?

**Problems with separate workflows:**
- ❌ Frontend and backend can get out of sync
- ❌ Failed backend + successful frontend = broken app
- ❌ No automatic rollback capability
- ❌ Difficult to track which versions are deployed together

**Benefits of unified workflow:**
- ✅ Atomic deployments (both or neither)
- ✅ Automatic rollback on failure
- ✅ Smoke tests verify end-to-end functionality
- ✅ Clear deployment history
- ✅ Version consistency guaranteed

## Workflow Steps

### 1. Setup Phase
- Checkout code
- Setup Python 3.12
- Setup Node.js 20
- Configure AWS credentials
- Setup AWS SAM CLI

### 2. Backend Build & Deploy
- Build backend with `sam build` (no container = 2-3 min)
- Deploy to Lambda via `sam deploy`
- **Fail fast:** If backend fails, stop immediately

### 3. Frontend Build
- Install dependencies with `npm ci`
- Build with Vite (with `VITE_API_URL` from secrets)

### 4. Frontend Backup
- Create timestamped backup of current frontend in S3
- Used for rollback if deployment fails

### 5. Frontend Deploy
- Sync built files to S3 bucket
- Invalidate CloudFront cache

### 6. Smoke Tests
- Wait 10 seconds for propagation
- Test backend health endpoint
- Test frontend via CloudFront
- **Fail if either test fails**

### 7. Rollback (if needed)
- If smoke tests fail, restore frontend from backup
- Invalidate CloudFront cache
- Log warning about backend (requires manual rollback)

## Build Time Optimization

**Original:** 20+ minutes (with `--use-container`)
**Optimized:** 2-3 minutes (without container)

The `--use-container` flag was removed because:
- Docker image pulling is slow in GitHub Actions
- ARM64 emulation adds significant overhead
- Native Python build is 10x faster
- Still produces valid Lambda packages for our simple dependencies

## Rollback Strategy

### Frontend Rollback (Automatic)
Frontend rollback is **automatic** if deployment fails:
1. Previous version backed up to S3 before deployment
2. On failure, restored from backup
3. CloudFront cache invalidated

### Backend Rollback (Manual)
Backend rollback requires **manual intervention**:

**Option 1: Revert Git Commit**
```bash
git revert HEAD
git push origin main
# Triggers new deployment with previous code
```

**Option 2: CloudFormation Rollback**
```bash
aws cloudformation describe-stack-events \
  --stack-name toallcreation-backend \
  --region us-west-2

# Find previous successful changeset and deploy it
```

**Option 3: Previous SAM Deployment**
```bash
cd backend
git checkout HEAD~1 -- .
sam build
sam deploy
```

## Deployment Triggers

**Automatic:**
- Push to `main` branch

**Manual:**
- GitHub Actions UI > "Run workflow" button

## Environment Variables

Required GitHub Secrets:
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `VITE_API_URL` - Backend API URL (for frontend build)
- `S3_BUCKET` - Frontend S3 bucket name
- `CLOUDFRONT_DISTRIBUTION_ID` - CloudFront distribution

## Monitoring Deployments

### Watch Live Deployment
```bash
gh run watch
```

### View Recent Deployments
```bash
gh run list --limit 5
```

### View Deployment Logs
```bash
gh run view <run-id> --log
```

### Check Deployment Status
```bash
# Backend
curl https://50gms3b8y2.execute-api.us-west-2.amazonaws.com/health

# Frontend
curl https://d1p7fiwu5m4weh.cloudfront.net
```

## Smoke Tests

The workflow includes basic smoke tests:

**Backend Health Check:**
```bash
curl https://50gms3b8y2.execute-api.us-west-2.amazonaws.com/health
# Expected: 200 OK with {"status": "healthy"}
```

**Frontend Availability:**
```bash
curl https://d1p7fiwu5m4weh.cloudfront.net
# Expected: 200 OK with HTML content
```

If either test fails, the workflow:
1. Marks the deployment as failed
2. Rolls back the frontend
3. Alerts via GitHub Actions UI

## Local Testing Before Deploy

**Always test locally before pushing to main:**

```bash
# Backend
cd backend
sam build
sam local start-api --port 3000
curl http://localhost:3000/health

# Frontend
cd frontend
npm install
npm run dev
# Visit http://localhost:5173 and test "Test Backend API" button
```

## Deployment Checklist

Before pushing to `main`:

- [ ] Test backend locally (`sam local start-api`)
- [ ] Test frontend locally (`npm run dev`)
- [ ] Run frontend build locally (`npm run build`)
- [ ] Verify `.env` files are NOT committed
- [ ] Check git diff to review changes
- [ ] Commit with descriptive message
- [ ] Push to `main`
- [ ] Monitor GitHub Actions workflow
- [ ] Verify smoke tests pass
- [ ] Test deployed app manually

## Emergency Stop

If a deployment is in progress and needs to be stopped:

```bash
# Cancel running workflow
gh run list
gh run cancel <run-id>

# Then manually rollback if needed (see Rollback Strategy above)
```

## Future Enhancements

Potential improvements for production:

1. **Blue-Green Deployment** - Deploy to separate stack, test, then switch traffic
2. **Canary Releases** - Gradually roll out to percentage of users
3. **Automated E2E Tests** - Full integration tests before marking successful
4. **Backend Rollback Automation** - CloudFormation changesets with auto-rollback
5. **Slack/Email Notifications** - Alert on deployment success/failure
6. **Deployment Approval** - Manual approval gate for production
7. **Multi-Environment** - Separate workflows for dev/staging/prod

## Troubleshooting

### Build Fails with "Module not found"
**Cause:** Missing dependency in requirements.txt or package.json
**Fix:** Add dependency locally, test, then push

### Backend Deploys but Frontend Fails
**Result:** Automatic frontend rollback to previous version
**Action:** Fix frontend issue, push again

### Frontend Deploys but Smoke Tests Fail
**Result:** Automatic frontend rollback
**Action:** Check if backend/frontend are compatible, fix and redeploy

### CloudFront Shows Old Version
**Cause:** Cache not invalidated or propagation delay
**Fix:** Wait 5-10 minutes or manually invalidate:
```bash
aws cloudfront create-invalidation \
  --distribution-id E2JDMDOIC3T6K6 \
  --paths "/*"
```

### Workflow Takes Too Long
**Current:** 2-3 minutes
**If slower:** Check GitHub Actions status page for incidents

## Cost Impact

**Unified deployment stays within AWS Free Tier:**
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free (12 months)
- S3: 5GB storage + 2000 PUT requests free (12 months)
- CloudFront: 1TB transfer + 10M requests free (always)
- **Deployment cost:** $0 (within free tier limits)

## References

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [CloudFormation Rollback](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-rollback-triggers.html)
