"""
MStock Authentication Module

This module handles authentication with the MStock (Mirae Asset) broker API.
Extends the BaseAuthenticator to provide MStock-specific authentication.
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from .base_auth import BaseAuthenticator

logger = logging.getLogger(__name__)

class MStockAuthenticator(BaseAuthenticator):
    """
    MStock (Mirae Asset) API Authenticator
    
    Handles 2-step authentication process:
    1. Login with username/password -> triggers OTP
    2. Exchange OTP + API key for access token
    """
    
    def __init__(self):
        """Initialize MStock authenticator"""
        super().__init__("mstock")  # This will look for MSTOCK_* env variables
        
        # MStock API settings
        self.base_url = "https://api.mstock.trade/openapi/typea"
        self.headers = {
            'X-Mirae-Version': '1',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Session data
        self.session_data = None
        
        logger.info("MStock authenticator initialized")
    
    def get_required_credential_keys(self) -> list:
        """
        Get list of required credential keys for environment variables
        BaseAuthenticator will look for MSTOCK_{KEY} in environment
        
        Returns:
            List of required credential key names
        """
        return [
            "API_KEY",      # Will look for MSTOCK_API_KEY
            "USERNAME",     # Will look for MSTOCK_USERNAME  
            "PASSWORD",     # Will look for MSTOCK_PASSWORD
            "CHECKSUM"      # Will look for MSTOCK_CHECKSUM (usually "L")
        ]
    
    def authenticate(self) -> Optional[str]:
        """
        Main MStock authentication flow
        
        Returns:
            str: Access token if successful, None if failed
        """
        try:
            logger.info("Starting MStock authentication...")
            
            # Step 1: Login to trigger OTP
            if not self._perform_login():
                return None
            
            # Step 2: Get OTP from user
            otp = self._get_otp_from_user()
            if not otp:
                return None
            
            # Step 3: Exchange OTP for access token
            access_token = self._exchange_otp_for_token(otp)
            if access_token:
                # Set token expiry (MStock tokens typically last 24 hours)
                self.token_expiry = datetime.now() + timedelta(hours=24)
                self.access_token = access_token
                
                logger.info("✅ MStock authentication successful")
                return access_token
            else:
                logger.error("❌ Failed to get access token")
                return None
                
        except Exception as e:
            logger.error(f"❌ MStock authentication failed: {e}")
            return None
    
    def is_token_valid(self) -> bool:
        """
        Check if current access token is still valid
        
        Returns:
            bool: True if token is valid
        """
        if not self.access_token:
            return False
            
        if not self.token_expiry:
            # If no expiry set, assume it's expired
            return False
            
        # Check if token has expired
        return datetime.now() < self.token_expiry
    
    def _perform_login(self) -> bool:
        """
        Step 1: Login with username/password to trigger OTP
        
        Returns:
            bool: True if login successful and OTP sent
        """
        try:
            username = self.credentials.get("USERNAME")
            password = self.credentials.get("PASSWORD")
            
            if not username or not password:
                logger.error("Username or password not provided")
                return False
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password
            }
            
            logger.info(f"Attempting login for user: {username}")
            
            # Make login request
            response = requests.post(
                f"{self.base_url}/connect/login",
                headers=self.headers,
                data=login_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    self.session_data = result.get('data', {})
                    logger.info("✅ Login successful, OTP sent to registered mobile")
                    
                    # Show user info
                    user_info = self.session_data
                    logger.info(f"User: {user_info.get('nm', 'Unknown')}")
                    logger.info(f"Client ID: {user_info.get('cid', 'Unknown')}")
                    
                    return True
                else:
                    error_msg = result.get('message', 'Login failed')
                    logger.error(f"❌ Login failed: {error_msg}")
                    return False
            else:
                logger.error(f"❌ Login request failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    def _get_otp_from_user(self) -> Optional[str]:
        """
        Get OTP from user input with 5-minute timeout
        
        Returns:
            str: OTP entered by user
        """
        try:
            import signal
            import sys
            
            print("\n" + "="*50)
            print("📱 MStock OTP Required")
            print("="*50)
            print("An OTP has been sent to your registered mobile number.")
            print("Please check your SMS and enter the OTP below.")
            print("⏰ You have 5 minutes to enter the OTP.")
            print("="*50)
            
            # Set up timeout handler
            def timeout_handler(signum, frame):
                print("\n❌ OTP entry timeout (5 minutes). Please try again.")
                raise TimeoutError("OTP entry timeout")
            
            # Set 5-minute timeout (300 seconds)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(300)
            
            try:
                otp = input("Enter OTP: ").strip()
                signal.alarm(0)  # Cancel the alarm
                
                if not otp:
                    logger.error("No OTP provided")
                    return None
                
                # MStock typically sends 3-digit OTPs
                if len(otp) < 3:
                    logger.error("OTP seems too short (minimum 3 digits)")
                    return None
                
                if not otp.isdigit():
                    logger.error("OTP should contain only numbers")
                    return None
                
                logger.info("✅ OTP received from user")
                return otp
                
            except TimeoutError:
                logger.error("❌ OTP entry timeout")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error getting OTP: {e}")
            return None
    
    def _exchange_otp_for_token(self, otp: str) -> Optional[str]:
        """
        Step 2: Exchange OTP for access token
        
        Args:
            otp: OTP received by user
            
        Returns:
            str: Access token if successful
        """
        try:
            api_key = self.credentials.get("API_KEY")
            checksum = self.credentials.get("CHECKSUM", "L")  # Default to "L"
            
            if not api_key:
                logger.error("API key not provided")
                return None
            
            # Prepare token exchange data
            token_data = {
                'api_key': api_key,
                'request_token': otp,  # OTP is the request token
                'checksum': checksum
            }
            
            logger.info("Exchanging OTP for access token...")
            
            # Make token request
            response = requests.post(
                f"{self.base_url}/session/token",
                headers=self.headers,
                data=token_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    data = result.get('data', {})
                    access_token = data.get('access_token')
                    
                    if access_token:
                        logger.info("✅ Access token obtained successfully")
                        
                        # Log user details
                        user_name = data.get('user_name', 'Unknown')
                        user_id = data.get('user_id', 'Unknown')
                        logger.info(f"Authenticated as: {user_name} (ID: {user_id})")
                        
                        return access_token
                    else:
                        logger.error("❌ No access token in response")
                        return None
                else:
                    error_msg = result.get('message', 'Token exchange failed')
                    logger.error(f"❌ Token exchange failed: {error_msg}")
                    return None
            else:
                logger.error(f"❌ Token request failed with status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Token exchange error: {e}")
            return None
    
    def test_token(self) -> bool:
        """
        Test if the access token works by making a simple API call
        
        Returns:
            bool: True if token works
        """
        if not self.access_token:
            return False
            
        try:
            api_key = self.credentials.get("API_KEY")
            
            # Test with fund summary API
            headers = {
                'X-Mirae-Version': '1',
                'Authorization': f'token {api_key}:{self.access_token}'
            }
            
            response = requests.get(
                f"{self.base_url}/user/fundsummary",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info("✅ MStock token test successful")
                    return True
                else:
                    logger.warning(f"❌ Token test failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.warning(f"❌ Token test failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Token test error: {e}")
            return False
    
    def get_authenticated_headers(self) -> Optional[Dict[str, str]]:
        """
        Get headers for authenticated requests
        
        Returns:
            Dict with authentication headers
        """
        if not self.access_token:
            logger.error("No access token available")
            return None
            
        api_key = self.credentials.get("API_KEY")
        if not api_key:
            logger.error("No API key available")
            return None
            
        return {
            'X-Mirae-Version': '1',
            'Authorization': f'token {api_key}:{self.access_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get user information using fund summary API
        
        Returns:
            Dict containing user information or None if failed
        """
        try:
            if not self.is_token_valid():
                logger.error("Not authenticated or token expired")
                return None
            
            headers = self.get_authenticated_headers()
            if not headers:
                return None
            
            response = requests.get(
                f"{self.base_url}/user/fundsummary",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    fund_data = result.get('data', [])
                    if fund_data:
                        # Extract user info from fund data
                        return {
                            'broker': 'MStock',
                            'available_balance': fund_data[0].get('AVAILABLE_BALANCE', '0'),
                            'used_amount': fund_data[0].get('AMOUNT_UTILIZED', '0'),
                            'total_balance': fund_data[0].get('SUM_OF_ALL', '0'),
                            'authenticated': True
                        }
                return None
            else:
                logger.error(f"User info request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

def create_mstock_authenticator() -> Optional[MStockAuthenticator]:
    """
    Factory function to create MStockAuthenticator
    
    Returns:
        MStockAuthenticator instance or None if credentials missing
    """
    try:
        authenticator = MStockAuthenticator()
        
        # Validate that required credentials are present
        if not authenticator.validate_credentials():
            logger.error("Missing required MStock credentials")
            return None
        
        return authenticator
        
    except Exception as e:
        logger.error(f"Failed to create MStock authenticator: {e}")
        return None