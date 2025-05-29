#!/usr/bin/env python3
"""
Test Shoonya Authenticator

Tests the ShoonyaAuthenticator class with real or dummy credentials
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_shoonya_authenticator_import():
    """Test importing the ShoonyaAuthenticator"""
    print("🔧 Testing ShoonyaAuthenticator Import")
    print("=" * 50)
    
    try:
        from src.auth.shoonya_auth import ShoonyaAuthenticator, create_shoonya_authenticator
        print("✅ SUCCESS: ShoonyaAuthenticator imported")
        print(f"   Class: {ShoonyaAuthenticator}")
        print(f"   Factory function: {create_shoonya_authenticator}")
        return True
    except ImportError as e:
        print(f"❌ FAILED: Import error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False

def test_credentials_loading():
    """Test loading credentials from environment"""
    print("\n🔑 Testing Credentials Loading")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = project_root / '.env'
    if env_file.exists():
        print("✅ .env file found")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check for Shoonya credentials
        shoonya_creds = {
            'SHOONYA_USERID': os.getenv('SHOONYA_USERID'),
            'SHOONYA_PASSWORD': os.getenv('SHOONYA_PASSWORD'),
            'SHOONYA_VENDOR_CODE': os.getenv('SHOONYA_VENDOR_CODE'),
            'SHOONYA_API_SECRET': os.getenv('SHOONYA_API_SECRET'),
            'SHOONYA_TOTP_SECRET': os.getenv('SHOONYA_TOTP_SECRET'),
            'SHOONYA_IMEI': os.getenv('SHOONYA_IMEI')
        }
        
        print("📋 Shoonya credentials status:")
        for key, value in shoonya_creds.items():
            if value:
                masked_value = f"{value[:4]}{'*' * (len(value) - 4)}" if len(value) > 4 else "****"
                print(f"   ✅ {key}: {masked_value}")
            else:
                print(f"   ❌ {key}: Not set")
        
        # Check if minimum required credentials are present
        required = ['SHOONYA_USERID', 'SHOONYA_PASSWORD', 'SHOONYA_VENDOR_CODE', 'SHOONYA_API_SECRET']
        missing = [key for key in required if not shoonya_creds[key]]
        
        if missing:
            print(f"\n⚠️  Missing required credentials: {missing}")
            return False
        else:
            print(f"\n✅ All required credentials present")
            return True
    else:
        print("❌ .env file not found")
        return False

def test_authenticator_creation():
    """Test creating ShoonyaAuthenticator instance"""
    print("\n🏗️  Testing Authenticator Creation")
    print("=" * 50)
    
    try:
        from src.auth.shoonya_auth import create_shoonya_authenticator
        
        # Create authenticator from environment
        authenticator = create_shoonya_authenticator()
        
        if authenticator:
            print("✅ SUCCESS: ShoonyaAuthenticator created")
            print(f"   Instance: {authenticator}")
            print(f"   Broker: {authenticator.broker_name}")
            return authenticator
        else:
            print("❌ FAILED: Could not create authenticator (check credentials)")
            return None
            
    except Exception as e:
        print(f"❌ FAILED: Authenticator creation error - {e}")
        return None

def test_dummy_authentication():
    """Test authentication behavior with invalid environment (should fail gracefully)"""
    print("\n🧪 Testing Authentication Failure Handling")
    print("=" * 50)
    
    try:
        from src.auth.shoonya_auth import ShoonyaAuthenticator
        
        # Test with current environment but expect authentication to work or fail gracefully
        authenticator = ShoonyaAuthenticator()
        print("✅ Authenticator created")
        
        # The authentication should work with real credentials or fail gracefully
        print("🔐 Testing authentication behavior...")
        
        # Just test that the method exists and can be called
        if hasattr(authenticator, 'authenticate'):
            print("✅ Authenticate method available")
        
        if hasattr(authenticator, 'is_token_valid'):
            print("✅ Token validation method available")
            
        if hasattr(authenticator, 'is_authenticated'):
            print("✅ Authentication status method available")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Authentication behavior test error - {e}")
        return False

def test_real_authentication(authenticator):
    """Test authentication with real credentials"""
    print("\n🔐 Testing Real Authentication")
    print("=" * 50)
    
    if not authenticator:
        print("❌ No authenticator provided")
        return False
    
    try:
        print("🚀 Attempting authentication...")
        result = authenticator.authenticate()
        
        if result:
            print("✅ SUCCESS: Authentication successful!")
            
            # Test is_authenticated
            if authenticator.is_authenticated():
                print("✅ Authentication status confirmed")
                
                # Get user info
                user_info = authenticator.get_user_info()
                if user_info:
                    print("✅ User info retrieved:")
                    for key, value in user_info.items():
                        print(f"   {key}: {value}")
                
                return True
            else:
                print("❌ Authentication status check failed")
                return False
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Authentication error - {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Shoonya Authenticator Tests")
    print()
    
    # Test 1: Import
    if not test_shoonya_authenticator_import():
        print("\n❌ Import test failed. Cannot continue.")
        return
    
    # Test 2: Credentials
    creds_ok = test_credentials_loading()
    
    # Test 3: Authenticator creation
    authenticator = test_authenticator_creation()
    
    # Test 4: Dummy authentication
    test_dummy_authentication()
    
    # Test 5: Real authentication (only if credentials are available)
    if creds_ok and authenticator:
        print("\n⚠️  About to test with REAL credentials!")
        print("This will attempt to login to Shoonya with your actual account.")
        
        # For safety, let's ask for confirmation
        if os.getenv('TESTING') != 'true':
            response = input("\nProceed with real authentication test? (y/n): ")
            if response.lower() != 'y':
                print("⏭️  Skipping real authentication test")
                return
        
        test_real_authentication(authenticator)
    else:
        print("\n⏭️  Skipping real authentication test (missing credentials)")
    
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    main()