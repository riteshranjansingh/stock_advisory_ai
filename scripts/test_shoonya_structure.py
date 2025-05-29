#!/usr/bin/env python3
"""
Test script to understand Shoonya package structure
"""

import sys
import logging

def test_shoonya_imports():
    """Test different ways to import Shoonya"""
    print("🔍 Testing Shoonya Package Structure")
    print("=" * 50)
    
    # Test 1: Try NorenRestApi direct import
    try:
        import NorenRestApi
        print("✅ SUCCESS: import NorenRestApi")
        print(f"   Package: {NorenRestApi}")
        print(f"   Dir: {dir(NorenRestApi)}")
    except ImportError as e:
        print(f"❌ FAILED: import NorenRestApi - {e}")
    
    print()
    
    # Test 2: Try NorenApi from NorenRestApi
    try:
        from NorenRestApi import NorenApi
        print("✅ SUCCESS: from NorenRestApi import NorenApi")
        print(f"   Class: {NorenApi}")
        print(f"   Methods: {[m for m in dir(NorenApi) if not m.startswith('_')][:10]}...")
    except ImportError as e:
        print(f"❌ FAILED: from NorenRestApi import NorenApi - {e}")
    
    print()
    
    # Test 3: Try ShoonyaApiPy pattern (from documentation)
    try:
        from NorenRestApi.NorenApi import NorenApi
        
        class ShoonyaApiPy(NorenApi):
            def __init__(self):
                NorenApi.__init__(
                    self, 
                    host='https://api.shoonya.com/NorenWClientTP/', 
                    websocket='wss://api.shoonya.com/NorenWSTP/'
                )
        
        api = ShoonyaApiPy()
        print("✅ SUCCESS: Created ShoonyaApiPy class")
        print(f"   API Instance: {api}")
        print(f"   Available methods: {[m for m in dir(api) if not m.startswith('_') and callable(getattr(api, m))][:10]}...")
        
    except Exception as e:
        print(f"❌ FAILED: ShoonyaApiPy creation - {e}")
    
    print()
    
    # Test 4: Check for login method
    try:
        from NorenRestApi.NorenApi import NorenApi
        
        class TestApi(NorenApi):
            def __init__(self):
                NorenApi.__init__(
                    self, 
                    host='https://api.shoonya.com/NorenWClientTP/', 
                    websocket='wss://api.shoonya.com/NorenWSTP/'
                )
        
        api = TestApi()
        
        if hasattr(api, 'login'):
            print("✅ SUCCESS: login method found")
            print(f"   Login method: {api.login}")
        else:
            print("❌ FAILED: No login method found")
            
        # Check other key methods
        key_methods = ['get_quotes', 'searchscrip', 'get_time_price_series']
        for method in key_methods:
            if hasattr(api, method):
                print(f"✅ Found method: {method}")
            else:
                print(f"❌ Missing method: {method}")
                
    except Exception as e:
        print(f"❌ FAILED: Method check - {e}")

def test_pyotp():
    """Test pyotp for TOTP generation"""
    print("\n🔐 Testing TOTP Generation")
    print("=" * 50)
    
    try:
        import pyotp
        
        # Test with a dummy secret
        dummy_secret = "JBSWY3DPEHPK3PXP"  # Standard test secret
        totp = pyotp.TOTP(dummy_secret)
        current_otp = totp.now()
        
        print("✅ SUCCESS: pyotp working")
        print(f"   Test OTP: {current_otp}")
        print(f"   OTP Length: {len(current_otp)}")
        
    except Exception as e:
        print(f"❌ FAILED: pyotp test - {e}")

if __name__ == "__main__":
    print("🚀 Starting Shoonya Package Structure Test")
    print()
    
    test_shoonya_imports()
    test_pyotp()
    
    print("\n✨ Test Complete!")