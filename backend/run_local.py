#!/usr/bin/env python3
"""
Run FastAPI backend locally for development
Usage: python run_local.py
"""
import os
import sys
import uvicorn

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set environment variables for local development
os.environ.setdefault('COGNITO_USER_POOL_ID', 'us-west-2_Sqr1Z6TnM')
os.environ.setdefault('COGNITO_APP_CLIENT_ID', '1ehjfin2vmmqfbvrcqr85pcita')
os.environ.setdefault('COGNITO_REGION', 'us-west-2')
os.environ.setdefault('SOCIAL_ACCOUNTS_TABLE', 'toallcreation-social-accounts')

# Load Facebook credentials from AWS SSM (will use deployed credentials)
# You could also set these directly for local testing:
# os.environ['FACEBOOK_CLIENT_ID'] = 'your_app_id'
# os.environ['FACEBOOK_CLIENT_SECRET'] = 'your_app_secret'

if __name__ == "__main__":
    print("🚀 Starting ToAllCreation Backend (Local Development)")
    print("📍 API will be available at: http://localhost:8000")
    print("📄 API Docs: http://localhost:8000/docs")
    print("\n⚠️  Note: OAuth callbacks will need to redirect to localhost:8000")
    print("    Update Facebook App OAuth redirect URI to:")
    print("    http://localhost:8000/api/social/callback\n")

    # Import and run the FastAPI app
    from main import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
