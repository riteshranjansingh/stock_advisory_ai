"""
Shoonya Authentication Module

This module handles authentication with the Shoonya (Finvasia) broker API.
Extends the BaseAuthenticator to provide Shoonya-specific authentication.
"""

import os
import logging
import pyotp
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from .base_auth import BaseAuthenticator

# Configure logging
logger = logging.getLogger(__name__)

class ShoonyaAuthenticator(BaseAuthenticator):
    """
    Shoonya (Finvasia) API Authenticator
    
    Handles session-based authentication with Shoonya broker.
    Unlike OAuth2, Shoonya uses simple session-based login with OTP/TOTP.
    """
    
    def __init__(self):
        """
        Initialize Shoonya authenticator
        Following BaseAuthenticator pattern - loads credentials from environment
        """
        super().__init__("shoonya")  # Pass broker name string, not credentials dict
        self.api_instance = None
        self.session_token = None
        
        logger.info("ShoonyaAuthenticator initialized")
    
    def get_required_credential_keys(self) -> list:
        """
        Get list of required credential keys for environment variables
        BaseAuthenticator will look for SHOONYA_{KEY} in environment
        
        Returns:
            List of required credential key names
        """
        return [
            "USERID",      # Will look for SHOONYA_USERID
            "PASSWORD",    # Will look for SHOONYA_PASSWORD  
            "VENDOR_CODE", # Will look for SHOONYA_VENDOR_CODE
            "API_SECRET",  # Will look for SHOONYA_API_SECRET
            "TOTP_SECRET", # Will look for SHOONYA_TOTP_SECRET (optional)
            "IMEI"         # Will look for SHOONYA_IMEI (optional)
        ]
    
    def authenticate(self) -> str:
        """
        Main authentication method - returns access token
        
        Returns:
            str: Session token if successful, None if failed
        """
        try:
            logger.info("Starting Shoonya authentication...")
            
            # Create API instance
            if not self._create_api_instance():
                return None
            
            # Perform login
            if not self._perform_login():
                return None
            
            # Store token for BaseAuthenticator compatibility
            self.access_token = self.session_token
            self.token_expiry = datetime.now() + timedelta(hours=24)  # Shoonya sessions last ~24 hours
            
            logger.info("✅ Shoonya authentication successful")
            return self.session_token
            
        except Exception as e:
            logger.error(f"❌ Shoonya authentication failed: {e}")
            return None
    
    def is_token_valid(self) -> bool:
        """
        Check if the current token/session is valid
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Check if we have API instance and session token
            if not self.api_instance or not self.session_token:
                return False
            
            # Try to make a simple API call to verify session
            response = self.api_instance.get_limits()
            
            if response and response.get('stat') == 'Ok':
                return True
            else:
                logger.warning("Session appears to be invalid")
                return False
                
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    def _create_api_instance(self) -> bool:
        """Create Shoonya API instance"""
        try:
            from NorenRestApiPy.NorenApi import NorenApi
            
            class ShoonyaApiPy(NorenApi):
                def __init__(self):
                    NorenApi.__init__(
                        self, 
                        host='https://api.shoonya.com/NorenWClientTP/', 
                        websocket='wss://api.shoonya.com/NorenWSTP/'
                    )
            
            self.api_instance = ShoonyaApiPy()
            logger.info("✅ Shoonya API instance created")
            return True
            
        except ImportError as e:
            logger.error(f"❌ Failed to import Shoonya API: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to create API instance: {e}")
            return False
    
    def _perform_login(self) -> bool:
        """Perform the actual login"""
        try:
            # Generate 2FA
            twoFA = self._generate_2fa()
            
            # Get credentials from BaseAuthenticator
            userid = self.credentials.get("USERID")
            password = self.credentials.get("PASSWORD")
            vendor_code = self.credentials.get("VENDOR_CODE")
            api_secret = self.credentials.get("API_SECRET")
            imei = self.credentials.get("IMEI") or "test12345"
            
            # Prepare login parameters
            login_params = {
                'userid': userid,
                'password': password,
                'twoFA': twoFA,
                'vendor_code': vendor_code,
                'api_secret': api_secret,
                'imei': imei
            }
            
            logger.info(f"Attempting login for user: {userid}")
            
            # Perform login
            response = self.api_instance.login(**login_params)
            
            # Check login response
            if response and response.get('stat') == 'Ok':
                self.session_token = response.get('susertoken', '')
                logger.info("✅ Login successful")
                return True
            else:
                error_msg = response.get('emsg', 'Unknown error') if response else 'No response'
                logger.error(f"❌ Login failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    def _generate_2fa(self) -> str:
        """
        Generate 2FA code
        
        Returns:
            str: 2FA code (OTP or TOTP)
        """
        # Check if TOTP secret is provided
        totp_secret = self.credentials.get("TOTP_SECRET")
        
        if totp_secret:
            try:
                totp = pyotp.TOTP(totp_secret)
                current_totp = totp.now()
                logger.info("✅ TOTP generated from secret")
                return current_totp
            except Exception as e:
                logger.error(f"❌ TOTP generation failed: {e}")
        
        # If no TOTP secret, ask for manual OTP
        logger.info("📱 Manual OTP required (no TOTP secret found)")
        return input("Enter OTP from your app: ") if not os.getenv('TESTING') else '123456'
    
    def get_authenticated_session(self) -> Optional[Any]:
        """
        Get the authenticated API instance for making requests
        
        Returns:
            The authenticated Shoonya API instance
        """
        if self.is_token_valid():
            return self.api_instance
        else:
            logger.warning("Not authenticated. Call get_access_token() first.")
            return None
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated (alias for is_token_valid for compatibility)
        
        Returns:
            bool: True if authenticated and session is valid
        """
        return self.is_token_valid()
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get user information
        
        Returns:
            Dict containing user information or None if failed
        """
        try:
            if not self.is_token_valid():
                logger.error("Not authenticated")
                return None
            
            # Get user limits which includes user info
            response = self.api_instance.get_limits()
            
            if response and response.get('stat') == 'Ok':
                return {
                    'user_id': self.credentials.get("USERID"),
                    'broker': 'Shoonya',
                    'account_id': response.get('actid', ''),
                    'cash_available': response.get('cash', '0'),
                    'margin_used': response.get('marginused', '0')
                }
            else:
                logger.error("Failed to get user info")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

def create_shoonya_authenticator() -> Optional[ShoonyaAuthenticator]:
    """
    Factory function to create ShoonyaAuthenticator
    
    Returns:
        ShoonyaAuthenticator instance or None if credentials missing
    """
    try:
        authenticator = ShoonyaAuthenticator()
        
        # Validate that required credentials are present
        if not authenticator.validate_credentials():
            logger.error("Missing required Shoonya credentials")
            return None
        
        return authenticator
        
    except Exception as e:
        logger.error(f"Failed to create Shoonya authenticator: {e}")
        return None