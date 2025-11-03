# CloudFront CDN Configuration

**Status:** ✅ DEPLOYED
**Date:** November 3, 2025

---

## 🌐 CloudFront URL (HTTPS Enabled!)

```
https://d1p7fiwu5m4weh.cloudfront.net
```

**Distribution ID:** `E2JDMDOIC3T6K6`

---

## ✅ Benefits

1. **HTTPS:** Free SSL/TLS certificate included
2. **Global CDN:** Content served from edge locations worldwide
3. **Caching:** Reduced load on S3, faster response times
4. **Compression:** Automatic gzip compression enabled
5. **Cost:** $0 within free tier (1 TB data transfer/month)

---

## 🎯 What Was Configured

### Origin
- **S3 Website:** toallcreation-frontend-271297706586.s3-website-us-west-2.amazonaws.com
- **Protocol:** HTTP only (S3 website endpoints don't support HTTPS)
- **Viewer Policy:** Redirect HTTP → HTTPS

### Cache Settings
- **Default TTL:** 24 hours (86400 seconds)
- **Max TTL:** 1 year
- **Min TTL:** 0 (respect origin cache headers)
- **Compression:** Enabled (gzip)

### Error Handling
- **404 Errors:** Redirected to `/index.html` with 200 status
  - Required for React Router SPA functionality
  - Ensures client-side routing works

---

## 🔄 Cache Invalidation (Cache Busting)

### After Frontend Updates

When you deploy new frontend code, invalidate the cache:

```bash
# Invalidate everything (use sparingly - 1,000 free per month)
aws cloudfront create-invalidation \
  --distribution-id E2JDMDOIC3T6K6 \
  --paths "/*"

# Invalidate specific files only (recommended)
aws cloudfront create-invalidation \
  --distribution-id E2JDMDOIC3T6K6 \
  --paths "/index.html" "/assets/*"
```

### Check Invalidation Status
```bash
aws cloudfront list-invalidations \
  --distribution-id E2JDMDOIC3T6K6
```

---

## 🚀 Deployment Workflow

### 1. Build Frontend
```bash
cd frontend
npm run build
```

### 2. Upload to S3
```bash
aws s3 sync dist/ s3://toallcreation-frontend-271297706586/ --delete
```

### 3. Invalidate CloudFront Cache
```bash
aws cloudfront create-invalidation \
  --distribution-id E2JDMDOIC3T6K6 \
  --paths "/*"
```

### 4. Wait for Deployment (~5-10 minutes)
```bash
# Check status
aws cloudfront get-distribution \
  --id E2JDMDOIC3T6K6 \
  --query 'Distribution.Status'

# Status will be "Deployed" when ready
```

---

## 💰 Cost Analysis

### Free Tier (12 months)
- Data Transfer: 1 TB/month ✅
- Requests: 10M/month ✅
- Invalidations: 1,000 paths/month ✅

### After 12 Months
- Data Transfer: 1 TB/month (Always Free) ✅
- Beyond 1 TB: ~$0.085/GB
- Requests: ~$0.0075 per 10,000

### For This Hello World App
- **Estimated traffic:** 1,000-10,000 requests/month
- **Data transfer:** 100 MB - 1 GB/month
- **Cost:** $0 (well within free tier) ✅

---

## 🔧 Advanced Configuration

### Custom Domain (Future)
To use a custom domain:
1. Purchase domain (Route 53 or external)
2. Request ACM certificate in `us-east-1`
3. Update CloudFront distribution with alias
4. Add CNAME record in DNS

### Cache Headers (Future)
Add cache headers in S3 objects:
```bash
# Set cache-control for immutable assets
aws s3 cp dist/assets/ s3://bucket/assets/ \
  --recursive \
  --cache-control "public, max-age=31536000, immutable"

# Set no-cache for index.html
aws s3 cp dist/index.html s3://bucket/index.html \
  --cache-control "public, max-age=0, must-revalidate"
```

---

## 📊 Monitoring

### CloudFront Metrics (CloudWatch)
```bash
# View requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=E2JDMDOIC3T6K6 \
  --start-time 2025-11-03T00:00:00Z \
  --end-time 2025-11-03T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### CloudFront Console
```
https://console.aws.amazon.com/cloudfront/v3/home#/distributions/E2JDMDOIC3T6K6
```

---

## 🧪 Testing

### Test CloudFront URL
```bash
# Test HTTPS (should work)
curl -I https://d1p7fiwu5m4weh.cloudfront.net

# Test HTTP (should redirect to HTTPS)
curl -I http://d1p7fiwu5m4weh.cloudfront.net
```

### Test in Browser
1. Open: https://d1p7fiwu5m4weh.cloudfront.net
2. Click "Test Backend API"
3. Should see response from Lambda

### Verify Caching
```bash
# Check cache headers
curl -I https://d1p7fiwu5m4weh.cloudfront.net

# Look for these headers:
# X-Cache: Hit from cloudfront (cached)
# X-Cache: Miss from cloudfront (not cached yet)
```

---

## 🔐 Security Features

### Enabled
- ✅ HTTPS everywhere (redirect HTTP → HTTPS)
- ✅ TLS 1.0+ support
- ✅ IPv6 enabled
- ✅ Compression enabled

### Optional (Future)
- AWS WAF (Web Application Firewall)
- Origin Access Identity (OAI) for S3
- Signed URLs for private content
- Geographic restrictions

---

## 🎯 GitHub Actions Integration

Update `.github/workflows/frontend-deploy.yml`:

```yaml
- name: Invalidate CloudFront
  run: |
    aws cloudfront create-invalidation \
      --distribution-id E2JDMDOIC3T6K6 \
      --paths "/*"
```

Add GitHub Secret:
```
CLOUDFRONT_DISTRIBUTION_ID=E2JDMDOIC3T6K6
```

---

## 📋 Quick Reference

| Item | Value |
|------|-------|
| **CloudFront URL** | https://d1p7fiwu5m4weh.cloudfront.net |
| **Distribution ID** | E2JDMDOIC3T6K6 |
| **Origin** | toallcreation-frontend-271297706586.s3-website-us-west-2.amazonaws.com |
| **Region** | Global (all edge locations) |
| **Status** | InProgress → Deployed (~15 min) |
| **Cache TTL** | 24 hours default |
| **SSL** | CloudFront default certificate |

---

## 🗑️ Cleanup (When Done)

```bash
# Disable distribution first
aws cloudfront get-distribution-config \
  --id E2JDMDOIC3T6K6 > /tmp/dist-config.json

# Edit config: Set "Enabled": false
# Then update:
aws cloudfront update-distribution \
  --id E2JDMDOIC3T6K6 \
  --if-match <ETag> \
  --distribution-config file:///tmp/dist-config.json

# Wait for deployment, then delete
aws cloudfront delete-distribution \
  --id E2JDMDOIC3T6K6 \
  --if-match <ETag>
```

---

## ✅ Deployment Status

The CloudFront distribution is currently deploying. This takes **10-15 minutes**.

**Current Status:** `InProgress`

Check status:
```bash
aws cloudfront get-distribution \
  --id E2JDMDOIC3T6K6 \
  --query 'Distribution.Status'
```

Once it shows `Deployed`, your HTTPS URL will be live! 🎉

---

*CloudFront provides enterprise-grade CDN with HTTPS, all within AWS Free Tier!*
