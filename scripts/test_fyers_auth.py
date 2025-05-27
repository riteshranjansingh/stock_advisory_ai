#!/usr/bin/env python3
"""
Test script for Fyers authentication system
This script will help you get your first access token
"""
import sys
import os
import logging

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auth.fyers_auth import FyersAuthenticator

# Simple logging setup
logging.basicConfig(level=logging.INFO)

def main():
    """Test Fyers authentication flow"""
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    print("🚀 Testing Fyers Authentication System")
    print("="*50)
    
    try:
        # Create authenticator
        auth = FyersAuthenticator()
        
        # Check credentials
        print("1. Checking credentials...")
        if not auth.validate_credentials():
            print("❌ Credential validation failed!")
            print("Please check your .env file has all required Fyers credentials:")
            for key in auth.get_required_credential_keys():
                env_key = f"FYERS_{key}"
                value = os.getenv(env_key)
                status = "✅" if value else "❌"
                print(f"   {status} {env_key}")
            return False
        
        print("✅ All credentials found!")
        
        # Get access token (this will handle existing token or new authentication)
        print("\n2. Getting access token...")
        access_token = auth.get_access_token()
        
        if access_token:
            print("✅ Successfully obtained access token!")
            print(f"Token (first 20 chars): {access_token[:20]}...")
            
            # Test the token
            print("\n3. Testing token with API call...")
            if auth.test_token():
                print("✅ Token works! Authentication successful!")
                
                # Show token info
                from src.auth.token_manager import TokenManager
                token_manager = TokenManager()
                stored_brokers = token_manager.list_stored_brokers()
                print(f"\n📊 Stored tokens for brokers: {stored_brokers}")
                
                return True
            else:
                print("❌ Token test failed!")
                return False
        else:
            print("❌ Failed to get access token!")
            return False
            
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")
        logger.error(f"Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Fyers authentication setup complete!")
        print("You can now use Fyers API for market data.")
    else:
        print("\n💡 Tips for troubleshooting:")
        print("1. Double-check your .env file credentials")
        print("2. Make sure you have a Fyers trading account")
        print("3. Verify your app settings in Fyers API portal")
        print("4. Check internet connection")
    
    sys.exit(0 if success else 1)