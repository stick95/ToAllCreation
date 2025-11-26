"""
SSM Parameter Store Helper
Fetches encrypted parameters at runtime
"""
import boto3
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global SSM client
ssm_client = None


def get_ssm_client():
    """Get or create SSM client"""
    global ssm_client
    if ssm_client is None:
        region = os.environ.get('AWS_REGION', 'us-west-2')
        ssm_client = boto3.client('ssm', region_name=region)
    return ssm_client


def get_parameter(parameter_name: str, with_decryption: bool = True) -> Optional[str]:
    """
    Get parameter from SSM Parameter Store

    Args:
        parameter_name: Full parameter name (e.g., /toallcreation/youtube/client_secret)
        with_decryption: Whether to decrypt SecureString parameters

    Returns:
        Parameter value or None if not found
    """
    try:
        client = get_ssm_client()
        response = client.get_parameter(
            Name=parameter_name,
            WithDecryption=with_decryption
        )
        return response['Parameter']['Value']
    except client.exceptions.ParameterNotFound:
        logger.error(f"SSM parameter not found: {parameter_name}")
        return None
    except Exception as e:
        logger.error(f"Error fetching SSM parameter {parameter_name}: {e}")
        return None


def get_youtube_client_secret() -> str:
    """Get YouTube client secret from SSM"""
    secret = get_parameter('/toallcreation/youtube/client_secret')
    if not secret:
        raise ValueError("YouTube client secret not configured in SSM")
    return secret
