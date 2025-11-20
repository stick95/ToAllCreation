"""
Fetch managed pages/accounts from social platforms
For platforms where users can post to Pages they manage (Facebook, LinkedIn)
"""
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FacebookPagesService:
    """Fetch Facebook Pages user manages"""

    @staticmethod
    def get_user_pages(access_token: str) -> List[Dict]:
        """
        Get all Facebook Pages the user manages

        Returns list of pages with:
        - id: Page ID
        - name: Page name
        - access_token: Page access token (different from user token!)
        - category: Page category
        """
        try:
            # Get pages user manages
            url = "https://graph.facebook.com/v18.0/me/accounts"
            params = {
                "access_token": access_token,
                "fields": "id,name,access_token,category,tasks"
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            pages = data.get("data", [])

            # Filter to only pages where user can CREATE_CONTENT
            managed_pages = []
            for page in pages:
                tasks = page.get("tasks", [])
                if "CREATE_CONTENT" in tasks or "MANAGE" in tasks:
                    managed_pages.append({
                        "id": page["id"],
                        "name": page["name"],
                        "access_token": page["access_token"],
                        "category": page.get("category", ""),
                        "platform": "facebook"
                    })

            return managed_pages

        except Exception as e:
            logger.error(f"Error fetching Facebook pages: {e}")
            return []


class InstagramAccountsService:
    """Fetch Instagram Business accounts linked to Facebook Pages"""

    @staticmethod
    def get_instagram_accounts(facebook_pages: List[Dict]) -> List[Dict]:
        """
        Get Instagram Business accounts linked to Facebook Pages

        Args:
            facebook_pages: List of Facebook pages from get_user_pages()

        Returns list of Instagram accounts with:
        - id: Instagram account ID
        - username: Instagram username
        - page_id: Associated Facebook Page ID
        - page_name: Associated Facebook Page name
        """
        instagram_accounts = []

        for page in facebook_pages:
            try:
                # Get Instagram account linked to this page
                url = f"https://graph.facebook.com/v18.0/{page['id']}"
                params = {
                    "fields": "instagram_business_account",
                    "access_token": page["access_token"]
                }

                response = requests.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                ig_account_id = data.get("instagram_business_account", {}).get("id")

                if ig_account_id:
                    # Get Instagram account details
                    ig_url = f"https://graph.facebook.com/v18.0/{ig_account_id}"
                    ig_params = {
                        "fields": "id,username",
                        "access_token": page["access_token"]
                    }

                    ig_response = requests.get(ig_url, params=ig_params)
                    ig_response.raise_for_status()
                    ig_data = ig_response.json()

                    username = ig_data.get("username")
                    instagram_accounts.append({
                        "id": ig_account_id,
                        "name": f"@{username}" if username else "Instagram Account",
                        "username": username,
                        "page_id": page["id"],
                        "page_name": page["name"],
                        "access_token": page["access_token"],
                        "platform": "instagram"
                    })

            except Exception as e:
                logger.error(f"Error fetching Instagram for page {page['id']}: {e}")
                continue

        return instagram_accounts


class LinkedInPagesService:
    """Fetch LinkedIn Company Pages (Organizations) user manages"""

    @staticmethod
    def get_user_organizations(access_token: str) -> List[Dict]:
        """
        Get LinkedIn Organizations (Company Pages) user can post to

        Returns list of organizations with:
        - id: Organization ID
        - name: Organization name
        - vanityName: LinkedIn vanity URL name
        """
        try:
            # Get organizations where user has admin/editor role
            url = "https://api.linkedin.com/v2/organizationalEntityAcls"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            params = {
                "q": "roleAssignee",
                "projection": "(elements*(organizationalTarget~(localizedName,vanityName)))"
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            organizations = []

            for element in data.get("elements", []):
                org_data = element.get("organizationalTarget~", {})
                org_id = element.get("organizationalTarget")

                if org_data and org_id:
                    organizations.append({
                        "id": org_id,
                        "name": org_data.get("localizedName"),
                        "vanityName": org_data.get("vanityName"),
                        "platform": "linkedin"
                    })

            return organizations

        except Exception as e:
            logger.error(f"Error fetching LinkedIn organizations: {e}")
            return []


class SocialPagesService:
    """Unified service to fetch pages/accounts user can post to"""

    @staticmethod
    def get_available_accounts(platform: str, access_token: str) -> List[Dict]:
        """
        Get all accounts/pages user can post to for a platform

        Args:
            platform: "facebook", "instagram", "linkedin", "twitter"
            access_token: User's OAuth access token

        Returns:
            List of accounts with id, name, and posting credentials
        """
        if platform == "facebook":
            return FacebookPagesService.get_user_pages(access_token)

        elif platform == "instagram":
            # Instagram requires Facebook pages first
            fb_pages = FacebookPagesService.get_user_pages(access_token)
            return InstagramAccountsService.get_instagram_accounts(fb_pages)

        elif platform == "linkedin":
            # LinkedIn can post to personal profile OR organizations
            orgs = LinkedInPagesService.get_user_organizations(access_token)
            # Add personal profile as an option
            personal = [{
                "id": "personal",
                "name": "Personal Profile",
                "platform": "linkedin"
            }]
            return personal + orgs

        elif platform == "twitter":
            # Twitter only posts to personal account
            return [{
                "id": "personal",
                "name": "Personal Account",
                "platform": "twitter"
            }]

        else:
            return []
