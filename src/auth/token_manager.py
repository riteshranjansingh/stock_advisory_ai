"""
Token Manager - Secure storage and retrieval of authentication tokens
Stores tokens in database with encryption for security
"""
import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class TokenManager:
    """
    Manages secure storage and retrieval of broker authentication tokens
    Uses database storage with encryption for security
    """
    
    def __init__(self):
        self.db_path = self._get_database_path()
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self._initialize_token_table()
    
    def _get_database_path(self) -> str:
        """Get path to the main database"""
        # Use the same database as the main system
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, "data", "databases", "trading_system.db")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for token security"""
        key_file = os.path.join(os.path.dirname(self.db_path), "token_key.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info("Generated new encryption key for token security")
            return key
    
    def _initialize_token_table(self):
        """Create tokens table if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auth_tokens (
                        broker TEXT PRIMARY KEY,
                        encrypted_token TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.debug("Token table initialized")
        except Exception as e:
            logger.error(f"Failed to initialize token table: {e}")
    
    def save_token(self, broker: str, token_data: Dict) -> bool:
        """
        Save encrypted token data for a broker
        
        Args:
            broker: Broker name (e.g., 'fyers', 'shoonya')
            token_data: Dictionary containing token info
        
        Returns:
            bool: Success status
        """
        try:
            # Encrypt token data
            token_json = json.dumps(token_data)
            encrypted_token = self.cipher.encrypt(token_json.encode())
            encrypted_token_str = base64.b64encode(encrypted_token).decode()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO auth_tokens 
                    (broker, encrypted_token, updated_at) 
                    VALUES (?, ?, ?)
                ''', (broker, encrypted_token_str, datetime.now().isoformat()))
                conn.commit()
                
            logger.info(f"Saved encrypted token for {broker}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save token for {broker}: {e}")
            return False
    
    def get_token(self, broker: str) -> Optional[Dict]:
        """
        Retrieve and decrypt token data for a broker
        
        Args:
            broker: Broker name
            
        Returns:
            Dict: Token data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT encrypted_token FROM auth_tokens WHERE broker = ?',
                    (broker,)
                )
                result = cursor.fetchone()
                
            if not result:
                logger.debug(f"No token found for {broker}")
                return None
            
            # Decrypt token data
            encrypted_token = base64.b64decode(result[0])
            decrypted_token = self.cipher.decrypt(encrypted_token)
            token_data = json.loads(decrypted_token.decode())
            
            logger.debug(f"Retrieved token for {broker}")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve token for {broker}: {e}")
            return None
    
    def delete_token(self, broker: str) -> bool:
        """
        Delete token for a broker
        
        Args:
            broker: Broker name
            
        Returns:
            bool: Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM auth_tokens WHERE broker = ?', (broker,))
                conn.commit()
                
            logger.info(f"Deleted token for {broker}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete token for {broker}: {e}")
            return False
    
    def list_stored_brokers(self) -> list:
        """Get list of brokers with stored tokens"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT broker FROM auth_tokens')
                results = cursor.fetchall()
                
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Failed to list stored brokers: {e}")
            return []
    
    def get_token_info(self, broker: str) -> Optional[Dict]:
        """
        Get token metadata without decrypting the actual token
        
        Args:
            broker: Broker name
            
        Returns:
            Dict: Token metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT broker, created_at, updated_at 
                    FROM auth_tokens WHERE broker = ?
                ''', (broker,))
                result = cursor.fetchone()
                
            if not result:
                return None
                
            return {
                'broker': result[0],
                'created_at': result[1],
                'updated_at': result[2]
            }
            
        except Exception as e:
            logger.error(f"Failed to get token info for {broker}: {e}")
            return None