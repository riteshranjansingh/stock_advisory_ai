"""
Base Authentication Class for All Brokers
Provides common authentication interface that all brokers inherit
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class BaseAuthenticator(ABC):
    """
    Base class for all broker authentication systems
    All broker authenticators (Fyers, Shoonya, etc.) inherit from this
    """
    
    def __init__(self, broker_name: str):
        self.broker_name = broker_name
        self.credentials = self._load_credentials()
        self.access_token = None
        self.token_expiry = None
        
    def _load_credentials(self) -> Dict[str, str]:
        """Load broker-specific credentials from environment variables"""
        credentials = {}
        required_keys = self.get_required_credential_keys()
        
        for key in required_keys:
            env_key = f"{self.broker_name.upper()}_{key}"
            value = os.getenv(env_key)
            if not value:
                logger.warning(f"Missing credential: {env_key}")
            credentials[key] = value
            
        return credentials
    
    @abstractmethod
    def get_required_credential_keys(self) -> list:
        """Return list of required credential keys for this broker"""
        pass
    
    @abstractmethod
    def authenticate(self) -> str:
        """
        Main authentication method - should return access token
        This is where broker-specific logic goes
        """
        pass
    
    @abstractmethod
    def is_token_valid(self) -> bool:
        """Check if current access token is still valid"""
        pass
    
    def get_access_token(self) -> Optional[str]:
        """
        Smart token getter - checks validity and refreshes if needed
        This is the main method other components will call
        """
        try:
            # First, try to load existing token
            if self.load_existing_token():
                if self.is_token_valid():
                    logger.info(f"Using existing valid {self.broker_name} token")
                    return self.access_token
                else:
                    logger.info(f"Existing {self.broker_name} token expired, re-authenticating")
            
            # If no valid token, authenticate
            logger.info(f"Authenticating with {self.broker_name}...")
            self.access_token = self.authenticate()
            
            if self.access_token:
                self.save_token()
                logger.info(f"Successfully authenticated with {self.broker_name}")
                return self.access_token
            else:
                logger.error(f"Failed to authenticate with {self.broker_name}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error for {self.broker_name}: {e}")
            return None
    
    def load_existing_token(self) -> bool:
        """Load existing token from storage - implemented by TokenManager"""
        from .token_manager import TokenManager
        token_manager = TokenManager()
        token_data = token_manager.get_token(self.broker_name)
        
        if token_data:
            self.access_token = token_data.get('access_token')
            expiry_str = token_data.get('expiry')
            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)
            return True
        return False
    
    def save_token(self):
        """Save token to storage"""
        if self.access_token:
            from .token_manager import TokenManager
            token_manager = TokenManager()
            
            # Default expiry to 24 hours if not set
            if not self.token_expiry:
                self.token_expiry = datetime.now() + timedelta(hours=24)
            
            token_data = {
                'access_token': self.access_token,
                'expiry': self.token_expiry.isoformat(),
                'broker': self.broker_name
            }
            
            token_manager.save_token(self.broker_name, token_data)
    
    def validate_credentials(self) -> bool:
        """Check if all required credentials are present"""
        required_keys = self.get_required_credential_keys()
        missing_keys = []
        
        for key in required_keys:
            if not self.credentials.get(key):
                missing_keys.append(f"{self.broker_name.upper()}_{key}")
        
        if missing_keys:
            logger.error(f"Missing credentials for {self.broker_name}: {missing_keys}")
            return False
        
        return True