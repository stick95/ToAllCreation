# GitHub Secrets Setup Guide

## Required Secrets

You need to add these secrets to your GitHub repository for the Actions workflow to work:

### Go to GitHub Repository Settings
1. Navigate to your repository: https://github.com/yourusername/ToAllCreation
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Add These Secrets

#### Backend/API Configuration
```
Name: VITE_API_URL
Value: https://50gms3b8y2.execute-api.us-west-2.amazonaws.com
```

#### Cognito Configuration
```
Name: VITE_COGNITO_USER_POOL_ID
Value: us-west-2_Sqr1Z6TnM
```

```
Name: VITE_COGNITO_CLIENT_ID
Value: 1ehjfin2vmmqfbvrcqr85pcita
```

```
Name: VITE_COGNITO_REGION
Value: us-west-2
```

#### S3 Bucket
```
Name: S3_BUCKET
Value: toallcreation-frontend-271297706586
```

#### CloudFront Distribution
```
Name: CLOUDFRONT_DISTRIBUTION_ID
Value: E2JDMDOIC3T6K6
```

#### AWS Credentials
These should already be set, but verify:

```
Name: AWS_ACCESS_KEY_ID
Value: [Your AWS Access Key]
```

```
Name: AWS_SECRET_ACCESS_KEY
Value: [Your AWS Secret Key]
```

## Verification

After adding all secrets, you should have **8 secrets** total:
- ✅ VITE_API_URL
- ✅ VITE_COGNITO_USER_POOL_ID
- ✅ VITE_COGNITO_CLIENT_ID
- ✅ VITE_COGNITO_REGION
- ✅ S3_BUCKET
- ✅ CLOUDFRONT_DISTRIBUTION_ID
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY

## Testing the Workflow

After adding the secrets:

1. Push to the `main` branch
2. Check the Actions tab: https://github.com/yourusername/ToAllCreation/actions
3. The workflow should:
   - ✅ Build backend with SAM
   - ✅ Deploy backend to AWS
   - ✅ Build frontend with Cognito config
   - ✅ Deploy frontend to S3
   - ✅ Invalidate CloudFront cache
   - ✅ Run smoke tests

## Notes

- The Cognito values (User Pool ID and Client ID) are **not secret** - they're public configuration
- However, we store them as secrets to keep deployment configuration in one place
- The AWS credentials **are secret** and should never be committed to the repository
