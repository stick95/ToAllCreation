"""
Social Media Account Management Module
Handles OAuth flows and account linking for FB, X, LinkedIn, Instagram
"""
import os
import boto3
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

# DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('SOCIAL_ACCOUNTS_TABLE', 'toallcreation-social-accounts')
table = dynamodb.Table(table_name)


class SocialPlatform(str, Enum):
    """Supported social media platforms"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"  # X (formerly Twitter)
    LINKEDIN = "linkedin"


class AccountType(str, Enum):
    """Type of social media account"""
    PERSONAL = "personal"  # Personal profile (Twitter)
    PAGE = "page"  # Facebook Page, LinkedIn Company Page
    BUSINESS = "business"  # Instagram Business Account


class SocialAccountManager:
    """Manage social media account connections"""

    @staticmethod
    def create_account(
        user_id: str,
        platform: SocialPlatform,
        platform_user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[int] = None,
        username: Optional[str] = None,
        profile_data: Optional[Dict] = None,
        account_type: AccountType = AccountType.PERSONAL,
        page_id: Optional[str] = None,
        page_name: Optional[str] = None,
        instagram_account_id: Optional[str] = None
    ) -> Dict:
        """
        Link a social media account to user

        Args:
            user_id: Cognito user ID
            platform: Social platform name
            platform_user_id: User's ID on the social platform
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            token_expires_at: Token expiration timestamp
            username: Platform username
            profile_data: Additional profile information

        Returns:
            Created account record
        """
        account_id = f"{platform}:{platform_user_id}"
        timestamp = int(datetime.utcnow().timestamp())

        item = {
            'user_id': user_id,
            'account_id': account_id,
            'platform': platform,
            'platform_user_id': platform_user_id,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expires_at': token_expires_at,
            'username': username,
            'account_type': account_type,
            'page_id': page_id,  # For Facebook Pages / LinkedIn Company Pages
            'page_name': page_name,
            'instagram_account_id': instagram_account_id,  # For Instagram Business accounts
            'profile_data': profile_data or {},
            'created_at': timestamp,
            'updated_at': timestamp,
            'is_active': True
        }

        table.put_item(Item=item)
        return item

    @staticmethod
    def get_account(user_id: str, account_id: str) -> Optional[Dict]:
        """Get a specific social account"""
        response = table.get_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            }
        )
        return response.get('Item')

    @staticmethod
    def list_accounts(user_id: str, platform: Optional[SocialPlatform] = None) -> List[Dict]:
        """
        List all social accounts for a user

        Args:
            user_id: Cognito user ID
            platform: Optional platform filter

        Returns:
            List of social accounts
        """
        response = table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={
                ':user_id': user_id
            }
        )

        accounts = response.get('Items', [])

        # Filter by platform if specified
        if platform:
            accounts = [acc for acc in accounts if acc.get('platform') == platform]

        # Remove sensitive tokens from response
        for account in accounts:
            account.pop('access_token', None)
            account.pop('refresh_token', None)

        return accounts

    @staticmethod
    def update_tokens(
        user_id: str,
        account_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[int] = None
    ) -> Dict:
        """Update OAuth tokens for an account"""
        timestamp = int(datetime.utcnow().timestamp())

        update_expression = "SET access_token = :token, updated_at = :timestamp"
        expression_values = {
            ':token': access_token,
            ':timestamp': timestamp
        }

        if refresh_token:
            update_expression += ", refresh_token = :refresh"
            expression_values[':refresh'] = refresh_token

        if token_expires_at:
            update_expression += ", token_expires_at = :expires"
            expression_values[':expires'] = token_expires_at

        response = table.update_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )

        return response.get('Attributes', {})

    @staticmethod
    def delete_account(user_id: str, account_id: str) -> bool:
        """Unlink a social account"""
        try:
            table.delete_item(
                Key={
                    'user_id': user_id,
                    'account_id': account_id
                }
            )
            return True
        except Exception as e:
            print(f"Error deleting account: {e}")
            return False

    @staticmethod
    def get_platform_token(user_id: str, platform: SocialPlatform) -> Optional[str]:
        """
        Get active access token for a platform
        Used when posting to social media
        """
        accounts = SocialAccountManager.list_accounts(user_id, platform)
        if not accounts:
            return None

        # Get the full account with tokens
        account_id = accounts[0].get('account_id')
        account = SocialAccountManager.get_account(user_id, account_id)

        # Check if token is expired
        expires_at = account.get('token_expires_at')
        if expires_at and expires_at < int(datetime.utcnow().timestamp()):
            # Token expired - would need to refresh here
            # For now, return None
            return None

        return account.get('access_token')
