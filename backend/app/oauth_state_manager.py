"""
OAuth State Manager using DynamoDB
Stores temporary OAuth state with TTL (auto-expires after 10 minutes)
"""
import boto3
import json
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OAuthStateManager:
    """Manage OAuth state in DynamoDB with TTL"""

    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def save_state(self, state_key: str, data: Dict[str, Any], ttl_minutes: int = 10):
        """
        Save OAuth state with TTL

        Args:
            state_key: Unique state identifier
            data: OAuth data to store
            ttl_minutes: Time to live in minutes (default 10)
        """
        try:
            # Calculate expiration time (10 minutes from now)
            ttl = int(time.time()) + (ttl_minutes * 60)

            item = {
                'state_key': state_key,
                'data': json.dumps(data),
                'ttl': ttl,
                'created_at': int(time.time())
            }

            self.table.put_item(Item=item)
            logger.info(f"Saved OAuth state: {state_key}")

        except Exception as e:
            logger.error(f"Error saving OAuth state: {e}")
            raise

    def get_state(self, state_key: str, delete_after_read: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get OAuth state

        Args:
            state_key: Unique state identifier
            delete_after_read: If True, deletes state after reading (default True)

        Returns:
            OAuth data dict or None if not found/expired
        """
        try:
            response = self.table.get_item(Key={'state_key': state_key})

            if 'Item' not in response:
                logger.warning(f"OAuth state not found: {state_key}")
                return None

            item = response['Item']

            # Check if expired (belt and suspenders - DynamoDB TTL takes up to 48h)
            if item['ttl'] < int(time.time()):
                logger.warning(f"OAuth state expired: {state_key}")
                self.delete_state(state_key)
                return None

            data = json.loads(item['data'])

            # Optionally delete after reading (one-time use)
            if delete_after_read:
                self.delete_state(state_key)

            return data

        except Exception as e:
            logger.error(f"Error getting OAuth state: {e}")
            return None

    def delete_state(self, state_key: str):
        """Delete OAuth state"""
        try:
            self.table.delete_item(Key={'state_key': state_key})
            logger.info(f"Deleted OAuth state: {state_key}")
        except Exception as e:
            logger.error(f"Error deleting OAuth state: {e}")
