#!/usr/bin/env python3
"""
Get Cognito Access Token for Testing

Usage:
    python get_cognito_token.py --email user@example.com --password YourPassword123!

Requirements:
    pip install boto3
"""
import os
import sys
import argparse
import json
import hmac
import hashlib
import base64

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Error: boto3 not installed. Install with: pip install boto3")
    sys.exit(1)


def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """
    Calculate SECRET_HASH for Cognito authentication
    Only needed if User Pool Client has a secret
    """
    message = bytes(username + client_id, 'utf-8')
    secret = bytes(client_secret, 'utf-8')
    dig = hmac.new(secret, msg=message, digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def authenticate_user(
    region: str,
    user_pool_id: str,
    client_id: str,
    username: str,
    password: str,
    client_secret: str = None
) -> dict:
    """
    Authenticate user with Cognito and get tokens

    Returns:
        dict with keys: AccessToken, IdToken, RefreshToken, ExpiresIn
    """
    client = boto3.client('cognito-idp', region_name=region)

    # Prepare authentication parameters
    auth_params = {
        'USERNAME': username,
        'PASSWORD': password
    }

    # Add SECRET_HASH if client has a secret
    if client_secret:
        auth_params['SECRET_HASH'] = get_secret_hash(username, client_id, client_secret)

    try:
        # Initiate authentication
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters=auth_params
        )

        # Check if we got tokens back
        if 'AuthenticationResult' in response:
            return response['AuthenticationResult']
        else:
            # May require additional challenges (MFA, new password, etc.)
            print(f"Challenge required: {response.get('ChallengeName')}")
            print(json.dumps(response, indent=2, default=str))
            return None

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']

        if error_code == 'NotAuthorizedException':
            print(f"Error: Authentication failed - {error_message}")
        elif error_code == 'UserNotFoundException':
            print(f"Error: User not found - {error_message}")
        elif error_code == 'UserNotConfirmedException':
            print(f"Error: User email not verified - {error_message}")
        else:
            print(f"Error: {error_code} - {error_message}")

        return None


def register_user(
    region: str,
    client_id: str,
    username: str,
    password: str,
    email: str,
    client_secret: str = None
) -> bool:
    """
    Register a new user in Cognito User Pool

    Returns:
        True if successful, False otherwise
    """
    client = boto3.client('cognito-idp', region_name=region)

    # Prepare sign-up parameters
    kwargs = {
        'ClientId': client_id,
        'Username': username,
        'Password': password,
        'UserAttributes': [
            {'Name': 'email', 'Value': email}
        ]
    }

    # Add SECRET_HASH if client has a secret
    if client_secret:
        kwargs['SecretHash'] = get_secret_hash(username, client_id, client_secret)

    try:
        response = client.sign_up(**kwargs)
        print(f"User registered successfully!")
        print(f"User Sub (ID): {response['UserSub']}")
        print(f"Email verification required: {not response.get('UserConfirmed', False)}")
        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error: {error_code} - {error_message}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Get Cognito access token for testing')

    parser.add_argument('--email', required=True, help='User email address')
    parser.add_argument('--password', required=True, help='User password')
    parser.add_argument('--register', action='store_true', help='Register new user instead of login')

    parser.add_argument('--region', default=os.getenv('AWS_REGION', 'us-west-2'), help='AWS region')
    parser.add_argument('--user-pool-id', default=os.getenv('COGNITO_USER_POOL_ID'), help='Cognito User Pool ID')
    parser.add_argument('--client-id', default=os.getenv('COGNITO_APP_CLIENT_ID'), help='Cognito App Client ID')
    parser.add_argument('--client-secret', default=os.getenv('COGNITO_APP_CLIENT_SECRET'), help='Cognito App Client Secret (if any)')

    args = parser.parse_args()

    # Validate required parameters
    if not args.user_pool_id:
        print("Error: COGNITO_USER_POOL_ID not provided")
        print("Set via --user-pool-id or COGNITO_USER_POOL_ID environment variable")
        sys.exit(1)

    if not args.client_id:
        print("Error: COGNITO_APP_CLIENT_ID not provided")
        print("Set via --client-id or COGNITO_APP_CLIENT_ID environment variable")
        sys.exit(1)

    print(f"Cognito User Pool: {args.user_pool_id}")
    print(f"App Client ID: {args.client_id}")
    print(f"Region: {args.region}")
    print(f"Email: {args.email}")
    print("")

    if args.register:
        # Register new user
        print("Registering new user...")
        success = register_user(
            region=args.region,
            client_id=args.client_id,
            username=args.email,
            password=args.password,
            email=args.email,
            client_secret=args.client_secret
        )

        if success:
            print("\nNext steps:")
            print("1. Check your email for verification code")
            print("2. Verify email via Cognito console or AWS CLI")
            print("3. Run this script again without --register to get token")
    else:
        # Authenticate user
        print("Authenticating...")
        result = authenticate_user(
            region=args.region,
            user_pool_id=args.user_pool_id,
            client_id=args.client_id,
            username=args.email,
            password=args.password,
            client_secret=args.client_secret
        )

        if result:
            print("\n" + "="*60)
            print("SUCCESS! Authentication tokens retrieved:")
            print("="*60)
            print(f"\nAccess Token (use for API calls):")
            print(f"{result['AccessToken'][:50]}...")
            print(f"\nID Token:")
            print(f"{result['IdToken'][:50]}...")
            print(f"\nRefresh Token:")
            print(f"{result['RefreshToken'][:50]}...")
            print(f"\nExpires in: {result.get('ExpiresIn', 3600)} seconds")

            print("\n" + "="*60)
            print("Test with curl:")
            print("="*60)
            print(f'export COGNITO_TOKEN="{result["AccessToken"]}"')
            print(f'curl -H "Authorization: Bearer $COGNITO_TOKEN" http://localhost:3000/api/profile')

            print("\n" + "="*60)
            print("Or run manual test script:")
            print("="*60)
            print(f'COGNITO_TOKEN="{result["AccessToken"]}" ./tests/manual_auth_test.sh')


if __name__ == '__main__':
    main()
