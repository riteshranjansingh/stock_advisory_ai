#!/usr/bin/env python3
"""
Test script for automated Fyers authentication
This will test the new localhost callback server
"""
import sys
import os
import logging

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auth.token_manager import TokenManager
from src.auth.fyers_auth import FyersAuthenticator

# Simple logging setup
logging.basicConfig(level=logging.INFO)

def main():
    """Test automated Fyers authentication flow"""
    
    print("🚀 Testing AUTOMATED Fyers Authentication")
    print("="*60)
    print("This will test the new localhost callback server!")
    print("No manual copy-paste required! 🎉")
    print("="*60)
    
    try:
        # Clear existing token to force fresh authentication
        print("\n1. Clearing existing token for fresh test...")
        token_manager = TokenManager()
        
        existing_brokers = token_manager.list_stored_brokers()
        if 'fyers' in existing_brokers:
            token_manager.delete_token('fyers')
            print("✅ Cleared existing Fyers token")
        else:
            print("ℹ️  No existing token found")
        
        # Test automated authentication
        print("\n2. Starting automated authentication...")
        print("📱 Browser will open automatically")
        print("🔐 Just login normally - everything else is automatic!")
        
        auth = FyersAuthenticator()
        access_token = auth.get_access_token()
        
        if access_token:
            print("\n🎉 AUTOMATED AUTHENTICATION SUCCESSFUL!")
            print(f"✅ Access token obtained: {access_token[:20]}...")
            
            # Test the token with API call
            print("\n3. Testing token with Fyers API...")
            if auth.test_token():
                print("✅ Token verified with Fyers API!")
                
                # Show stored tokens
                stored_brokers = token_manager.list_stored_brokers()
                print(f"📊 Stored tokens: {stored_brokers}")
                
                print("\n🏆 COMPLETE SUCCESS!")
                print("Your automated authentication system is working perfectly!")
                return True
            else:
                print("❌ Token test failed!")
                return False
        else:
            print("❌ Failed to get access token!")
            return False
            
    except Exception as e:
        print(f"❌ Error during automated authentication: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Automated Fyers Authentication Test")
    print("="*40)
    
    success = main()
    
    if success:
        print("\n🎊 CONGRATULATIONS!")
        print("Your professional-grade automated authentication is working!")
        print("✨ No more manual copy-paste required!")
        print("🚀 Ready for production trading system!")
    else:
        print("\n🔧 Troubleshooting Tips:")
        print("1. Check if port 8923 is available")
        print("2. Verify .env has 127.0.0.1 redirect URL") 
        print("3. Confirm Fyers app settings match redirect URL")
        print("4. Check internet connection")
    
    print("\n" + "="*40)
    sys.exit(0 if success else 1)