#!/usr/bin/env python3
"""
Test script for MStock authentication system
This script will help you get your first MStock access token
"""
import sys
import os
import logging

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auth.mstock_auth import MStockAuthenticator

# Simple logging setup
logging.basicConfig(level=logging.INFO)

def main():
    """Test MStock authentication flow"""
    
    print("🚀 Testing MStock Authentication System")
    print("="*50)
    
    try:
        # Create authenticator
        auth = MStockAuthenticator()
        
        # Check credentials
        print("1. Checking credentials...")
        if not auth.validate_credentials():
            print("❌ Credential validation failed!")
            print("Please check your .env file has all required MStock credentials:")
            for key in auth.get_required_credential_keys():
                env_key = f"MSTOCK_{key}"
                value = os.getenv(env_key)
                status = "✅" if value else "❌"
                masked_value = "***" if value else "MISSING"
                print(f"   {status} {env_key}: {masked_value}")
            
            print("\n💡 Setup Instructions:")
            print("1. Go to trade.mstock.com to generate your API key")
            print("2. Add the following to your .env file:")
            print("   MSTOCK_API_KEY=your_api_key")
            print("   MSTOCK_USERNAME=your_username")  
            print("   MSTOCK_PASSWORD=your_password")
            print("   MSTOCK_CHECKSUM=L")
            print("3. Make sure you have an active MStock trading account")
            return False
        
        print("✅ All credentials found!")
        
        # Show authentication steps
        print("\n📋 MStock Authentication Process:")
        print("1. Login with username/password → triggers OTP to your mobile")
        print("2. Enter OTP when prompted (5-minute timeout)")
        print("3. Exchange OTP for access token")
        print("4. Test token with API call")
        
        # Get access token (this will handle existing token or new authentication)
        print("\n2. Starting authentication process...")
        print("📱 Note: You'll receive an OTP on your registered mobile number")
        
        access_token = auth.get_access_token()
        
        if access_token:
            print("✅ Successfully obtained access token!")
            print(f"Token (first 20 chars): {access_token[:20]}...")
            
            # Test the token
            print("\n3. Testing token with API call...")
            if auth.test_token():
                print("✅ Token works! Authentication successful!")
                
                # Get user info
                user_info = auth.get_user_info()
                if user_info:
                    print("\n👤 Account Information:")
                    print(f"   Broker: {user_info.get('broker', 'Unknown')}")
                    print(f"   Available Balance: ₹{user_info.get('available_balance', '0')}")
                    print(f"   Used Amount: ₹{user_info.get('used_amount', '0')}")
                
                # Show token storage info
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
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Authentication cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")
        logging.error(f"Authentication test failed: {e}")
        return False

def show_troubleshooting_tips():
    """Show troubleshooting information"""
    print("\n🔧 Troubleshooting Tips:")
    print("="*30)
    print("1. Ensure you have an active MStock trading account")
    print("2. Verify your API key is correctly generated from trade.mstock.com")
    print("3. Check that your username/password are correct")
    print("4. Make sure your mobile number is registered with MStock")
    print("5. Check your SMS for the OTP (it may take a few minutes)")
    print("6. Ensure stable internet connection")
    print("7. Try logging into MStock web/app to verify credentials")
    
    print("\n📞 MStock Support:")
    print("- Website: https://www.miraeassetcm.com/")
    print("- Trading Platform: https://trade.mstock.com/")
    print("- For API issues, contact MStock support")

if __name__ == "__main__":
    print("🏦 MStock Authentication Test")
    print("="*40)
    
    success = main()
    
    if success:
        print("\n🎉 MStock authentication setup complete!")
        print("You can now use MStock API for market data.")
        print("✨ Token is stored securely and will be reused until expiry.")
    else:
        show_troubleshooting_tips()
    
    print("\n" + "="*40)
    sys.exit(0 if success else 1)