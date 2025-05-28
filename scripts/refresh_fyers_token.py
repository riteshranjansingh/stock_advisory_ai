#!/usr/bin/env python3
"""
Refresh expired Fyers token
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auth.token_manager import TokenManager
from src.auth.fyers_auth import FyersAuthenticator

def main():
    print("🔄 Refreshing Fyers Token")
    print("="*40)
    
    # Delete expired token
    token_manager = TokenManager()
    token_manager.delete_token('fyers')
    print("✅ Cleared expired token")
    
    # Get fresh token
    print("\n🔐 Getting fresh authentication...")
    auth = FyersAuthenticator()
    access_token = auth.get_access_token()
    
    if access_token:
        print("✅ Successfully obtained fresh token!")
        print(f"Token (first 20 chars): {access_token[:20]}...")
        
        # Test the token
        if auth.test_token():
            print("✅ Token verified - ready to use!")
            return True
        else:
            print("❌ Token test failed")
            return False
    else:
        print("❌ Failed to get fresh token")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Token refresh complete! You can now run other scripts.")
    else:
        print("\n❌ Token refresh failed. Please check your credentials.")