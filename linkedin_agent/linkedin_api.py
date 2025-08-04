import os
from typing import Dict, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from linkedin_v2.linkedin import LinkedInApplication
from linkedin_v2.exceptions import LinkedInError


class LinkedInAPI:
    """Class to handle LinkedIn API interactions."""
    
    def __init__(self, token_file: Optional[str] = None):
        """Initialize the LinkedIn API client.
        
        Args:
            token_file: Path to the file containing LinkedIn OAuth tokens.
                        If None, will look for tokens in environment variables.
        """
        self.client = None
        self.token_file = token_file or os.path.join(os.path.dirname(__file__), "linkedin_tokens.json")
        
        # Try to load tokens from file
        self._load_tokens()
    
    def _load_tokens(self) -> None:
        """Load LinkedIn OAuth tokens from file or environment variables."""
        # First try to load from file
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r") as f:
                    tokens = json.load(f)
                
                # Initialize the LinkedIn client with the loaded tokens
                self.client = LinkedInApplication(token=tokens.get("access_token"))
                return
            except Exception as e:
                print(f"Error loading LinkedIn tokens from file: {str(e)}")
        
        # If file loading failed, try environment variables
        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        refresh_token = os.environ.get("LINKEDIN_REFRESH_TOKEN")
        client_id = os.environ.get("LINKEDIN_CLIENT_ID")
        client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
        
        if access_token:
            # Initialize with just the token
            self.client = LinkedInApplication(token=access_token)
    
    def _save_tokens(self, tokens: Dict[str, str]) -> None:
        """Save LinkedIn OAuth tokens to file.
        
        Args:
            tokens: Dictionary containing the OAuth tokens.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            
            # Save tokens to file
            with open(self.token_file, "w") as f:
                json.dump(tokens, f)
        except Exception as e:
            print(f"Error saving LinkedIn tokens to file: {str(e)}")
    
    def authenticate(self, auth_code: str, redirect_uri: str) -> bool:
        """Authenticate with LinkedIn using OAuth 2.0.
        
        Args:
            auth_code: Authorization code from OAuth flow.
            redirect_uri: Redirect URI used in the OAuth flow.
            
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        try:
            # Initialize the LinkedIn client with client ID and secret from environment variables
            client_id = os.environ.get("LINKEDIN_CLIENT_ID")
            client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                raise ValueError("LinkedIn client ID and secret must be set in environment variables.")
            
            # Import the LinkedInAuthentication class
            from linkedin_v2.linkedin import LinkedInAuthentication
            
            # Create authentication object
            authentication = LinkedInAuthentication(
                client_id,
                client_secret,
                redirect_uri,
                ["r_liteprofile", "r_emailaddress", "w_member_social"]
            )
            
            # Set the authorization code
            authentication.authorization_code = auth_code
            
            # Exchange the authorization code for access and refresh tokens
            tokens = authentication.get_access_token()
            
            # Save the tokens
            self._save_tokens({
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
                "client_id": client_id,
                "client_secret": client_secret
            })
            
            # Initialize the client with the new tokens
            self.client = LinkedInApplication(token=tokens.get("access_token"))
            
            return True
        except Exception as e:
            print(f"Error authenticating with LinkedIn: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise.
        """
        if not self.client:
            return False
        
        try:
            # Try to get the current user's profile to check if the token is valid
            self.client.get_profile()
            return True
        except Exception:
            return False
    
    def get_auth_url(self, redirect_uri: str) -> str:
        """Get the LinkedIn OAuth authorization URL.
        
        Args:
            redirect_uri: Redirect URI for the OAuth flow.
            
        Returns:
            str: Authorization URL.
        """
        # Initialize the LinkedIn client with client ID and secret from environment variables
        client_id = os.environ.get("LINKEDIN_CLIENT_ID")
        client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise ValueError("LinkedIn client ID and secret must be set in environment variables.")
        
        # Import the LinkedInAuthentication class
        from linkedin_v2.linkedin import LinkedInAuthentication
        
        # Create authentication object
        authentication = LinkedInAuthentication(
            client_id,
            client_secret,
            redirect_uri,
            ["r_liteprofile", "r_emailaddress", "w_member_social"]
        )
        
        # Get the authorization URL
        return authentication.authorization_url
    
    def post_article(self, title: str, content: str) -> str:
        """Post an article to LinkedIn.
        
        Args:
            title: Title of the article.
            content: Content of the article.
            
        Returns:
            str: URL of the posted article.
            
        Raises:
            ValueError: If the client is not authenticated.
            LinkedInError: If there's an error posting the article.
        """
        if not self.client:
            raise ValueError("LinkedIn client is not authenticated.")
        
        try:
            # Create a share on LinkedIn
            response = self.client.submit_share(
                comment=title,
                text=content,
                visibility="PUBLIC"
            )
            
            # Extract the post URL from the response
            # Note: The actual response format may vary, adjust as needed
            activity_id = response.get("id", "")
            if activity_id:
                # Construct the post URL from the activity ID
                return f"https://www.linkedin.com/feed/update/{activity_id}/"
            else:
                return "Post created, but URL not available"
        except LinkedInError as e:
            raise e
        except Exception as e:
            raise LinkedInError(f"Error posting to LinkedIn: {str(e)}")