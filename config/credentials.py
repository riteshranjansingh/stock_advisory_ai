"""
Secure Credentials Manager
Handles API keys and secrets for different brokers safely
"""

import os
from typing import Dict, Optional, Any
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class CredentialsManager:
    """Manages broker credentials securely"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.credentials = {}
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from environment variables"""
        # Fyers credentials
        fyers_creds = self._load_fyers_credentials()
        if fyers_creds:
            self.credentials['fyers'] = fyers_creds
        
        # Shoonya credentials  
        shoonya_creds = self._load_shoonya_credentials()
        if shoonya_creds:
            self.credentials['shoonya'] = shoonya_creds
        
        # MStock credentials
        mstock_creds = self._load_mstock_credentials()
        if mstock_creds:
            self.credentials['mstock'] = mstock_creds
        
        # Upstox credentials
        upstox_creds = self._load_upstox_credentials()
        if upstox_creds:
            self.credentials['upstox'] = upstox_creds
        
        # Dhan credentials
        dhan_creds = self._load_dhan_credentials()
        if dhan_creds:
            self.credentials['dhan'] = dhan_creds
        
        # Kite/Zerodha credentials
        kite_creds = self._load_kite_credentials()
        if kite_creds:
            self.credentials['kite'] = kite_creds
        
        self.logger.info(f"Loaded credentials for {len(self.credentials)} brokers")
    
    def _load_fyers_credentials(self) -> Optional[Dict[str, str]]:
        """Load Fyers API credentials"""
        client_id = os.getenv('FYERS_CLIENT_ID')
        access_token = os.getenv('FYERS_ACCESS_TOKEN')
        
        if client_id and access_token:
            return {
                'client_id': client_id,
                'access_token': access_token,
                'broker_name': 'Fyers'
            }
        return None
    
    def _load_shoonya_credentials(self) -> Optional[Dict[str, str]]:
        """Load Shoonya API credentials"""
        user_id = os.getenv('SHOONYA_USER_ID')
        password = os.getenv('SHOONYA_PASSWORD')
        totp_key = os.getenv('SHOONYA_TOTP_KEY')  # For 2FA
        api_key = os.getenv('SHOONYA_API_KEY')
        
        if user_id and password and api_key:
            return {
                'user_id': user_id,
                'password': password,
                'totp_key': totp_key,
                'api_key': api_key,
                'broker_name': 'Shoonya'
            }
        return None
    
    def _load_mstock_credentials(self) -> Optional[Dict[str, str]]:
        """Load MStock API credentials"""
        client_code = os.getenv('MSTOCK_CLIENT_CODE')
        password = os.getenv('MSTOCK_PASSWORD')
        totp_key = os.getenv('MSTOCK_TOTP_KEY')
        
        if client_code and password:
            return {
                'client_code': client_code,
                'password': password,
                'totp_key': totp_key,
                'broker_name': 'MStock'
            }
        return None
    
    def _load_upstox_credentials(self) -> Optional[Dict[str, str]]:
        """Load Upstox API credentials"""
        api_key = os.getenv('UPSTOX_API_KEY')
        api_secret = os.getenv('UPSTOX_API_SECRET')
        access_token = os.getenv('UPSTOX_ACCESS_TOKEN')
        
        if api_key and api_secret:
            return {
                'api_key': api_key,
                'api_secret': api_secret,
                'access_token': access_token,
                'broker_name': 'Upstox'
            }
        return None
    
    def _load_dhan_credentials(self) -> Optional[Dict[str, str]]:
        """Load Dhan API credentials"""
        client_id = os.getenv('DHAN_CLIENT_ID')
        access_token = os.getenv('DHAN_ACCESS_TOKEN')
        
        if client_id and access_token:
            return {
                'client_id': client_id,
                'access_token': access_token,
                'broker_name': 'Dhan'
            }
        return None
    
    def _load_kite_credentials(self) -> Optional[Dict[str, str]]:
        """Load Kite/Zerodha API credentials"""
        api_key = os.getenv('KITE_API_KEY')
        api_secret = os.getenv('KITE_API_SECRET')
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if api_key and api_secret:
            return {
                'api_key': api_key,
                'api_secret': api_secret,
                'access_token': access_token,
                'broker_name': 'Kite'
            }
        return None
    
    def get_credentials(self, broker_name: str) -> Optional[Dict[str, str]]:
        """Get credentials for a specific broker"""
        broker_name = broker_name.lower()
        return self.credentials.get(broker_name)
    
    def has_credentials(self, broker_name: str) -> bool:
        """Check if credentials exist for a broker"""
        return broker_name.lower() in self.credentials
    
    def get_available_brokers(self) -> list:
        """Get list of brokers with available credentials"""
        return list(self.credentials.keys())
    
    def validate_credentials(self, broker_name: str) -> bool:
        """Validate that all required credentials are present"""
        creds = self.get_credentials(broker_name)
        if not creds:
            return False
        
        # Check required fields based on broker
        if broker_name.lower() == 'fyers':
            return all(key in creds for key in ['client_id', 'access_token'])
        elif broker_name.lower() == 'shoonya':
            return all(key in creds for key in ['user_id', 'password', 'api_key'])
        elif broker_name.lower() == 'upstox':
            return all(key in creds for key in ['api_key', 'api_secret'])
        # Add more broker validations as needed
        
        return True
    
    def mask_sensitive_data(self, credentials: Dict[str, str]) -> Dict[str, str]:
        """Return credentials with sensitive data masked for logging"""
        masked = {}
        for key, value in credentials.items():
            if key in ['password', 'access_token', 'api_secret', 'totp_key']:
                masked[key] = '*' * 8 if value else None
            else:
                masked[key] = value
        return masked
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all configured brokers"""
        status = {
            'total_brokers_configured': len(self.credentials),
            'available_brokers': [],
            'missing_brokers': []
        }
        
        all_supported_brokers = ['fyers', 'shoonya', 'mstock', 'upstox', 'dhan', 'kite']
        
        for broker in all_supported_brokers:
            if self.has_credentials(broker):
                status['available_brokers'].append({
                    'name': broker,
                    'valid': self.validate_credentials(broker),
                    'credentials': self.mask_sensitive_data(self.get_credentials(broker))
                })
            else:
                status['missing_brokers'].append(broker)
        
        return status

# Global instance
credentials_manager = CredentialsManager()

# Convenience functions
def get_broker_credentials(broker_name: str) -> Optional[Dict[str, str]]:
    """Get credentials for a broker"""
    return credentials_manager.get_credentials(broker_name)

def has_broker_credentials(broker_name: str) -> bool:
    """Check if broker credentials are available"""
    return credentials_manager.has_credentials(broker_name)

def get_available_brokers() -> list:
    """Get list of available brokers"""
    return credentials_manager.get_available_brokers()