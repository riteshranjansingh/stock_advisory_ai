#!/usr/bin/env python3
"""
Test basic Shoonya API connection setup
"""

def test_shoonya_class_creation():
    """Test creating the Shoonya API class"""
    print("🔧 Testing Shoonya API Class Creation")
    print("=" * 50)
    
    try:
        from NorenRestApiPy.NorenApi import NorenApi
        print("✅ SUCCESS: Imported NorenApi class")
        print(f"   Class: {NorenApi}")
        
        # Check the class structure
        class_methods = [method for method in dir(NorenApi) if not method.startswith('_')]
        print(f"   Available methods: {class_methods[:15]}...")
        
        # Look for key methods
        key_methods = ['login', 'get_quotes', 'searchscrip', 'get_time_price_series']
        found_methods = []
        for method in key_methods:
            if method in class_methods:
                found_methods.append(method)
                print(f"   ✅ Found: {method}")
            else:
                print(f"   ❌ Missing: {method}")
        
        print()
        
        # Try to create instance
        try:
            # Based on documentation pattern: host and websocket URLs
            api = NorenApi(
                host='https://api.shoonya.com/NorenWClientTP/', 
                websocket='wss://api.shoonya.com/NorenWSTP/'
            )
            print("✅ SUCCESS: Created NorenApi instance")
            print(f"   Instance: {api}")
            
            # Check if login method exists and its signature
            if hasattr(api, 'login'):
                import inspect
                login_signature = inspect.signature(api.login)
                print(f"   Login signature: {login_signature}")
            
        except Exception as e:
            print(f"❌ FAILED: Instance creation - {e}")
            
            # Try without parameters
            try:
                api = NorenApi()
                print("✅ SUCCESS: Created NorenApi instance (no params)")
                print(f"   Instance: {api}")
            except Exception as e2:
                print(f"❌ FAILED: Instance creation (no params) - {e2}")
        
    except ImportError as e:
        print(f"❌ FAILED: Import error - {e}")

def test_shoonya_wrapper_class():
    """Test creating a Shoonya wrapper class like in documentation"""
    print("\n🔧 Testing Shoonya Wrapper Class")
    print("=" * 50)
    
    try:
        from NorenRestApiPy.NorenApi import NorenApi
        
        class ShoonyaApiPy(NorenApi):
            def __init__(self):
                NorenApi.__init__(
                    self, 
                    host='https://api.shoonya.com/NorenWClientTP/', 
                    websocket='wss://api.shoonya.com/NorenWSTP/'
                )
                print("   📡 API endpoints configured")
        
        # Create instance
        api = ShoonyaApiPy()
        print("✅ SUCCESS: Created ShoonyaApiPy wrapper")
        print(f"   Wrapper instance: {api}")
        
        # Test login method availability
        if hasattr(api, 'login'):
            print("   ✅ Login method available")
            
            # Try to understand login parameters (without actually calling it)
            import inspect
            try:
                login_sig = inspect.signature(api.login)
                print(f"   📝 Login parameters: {login_sig}")
            except:
                pass
        
        return api
        
    except Exception as e:
        print(f"❌ FAILED: Wrapper creation - {e}")
        return None

def show_expected_credentials():
    """Show what credentials we expect to need"""
    print("\n🔑 Expected Shoonya Credentials")
    print("=" * 50)
    
    credentials_info = {
        "userid": "Your Shoonya user ID",
        "password": "Your Shoonya password", 
        "twoFA": "OTP/TOTP (6-digit code)",
        "vendor_code": "Vendor code from Shoonya",
        "api_secret": "API secret/key from Shoonya",
        "imei": "Unique identifier (can be dummy like 'test12345')"
    }
    
    for key, desc in credentials_info.items():
        print(f"   {key}: {desc}")
    
    print("\n💡 These would go in your .env file:")
    for key in credentials_info.keys():
        env_key = f"SHOONYA_{key.upper()}"
        print(f"   {env_key}=your_value_here")

if __name__ == "__main__":
    print("🚀 Testing Shoonya Basic Connection Setup")
    print()
    
    test_shoonya_class_creation()
    api_instance = test_shoonya_wrapper_class()
    show_expected_credentials()
    
    print("\n✨ Basic Setup Test Complete!")
    print("\n📋 Next Steps:")
    print("   1. Share your working login code from previous chat")
    print("   2. Add Shoonya credentials to .env file")
    print("   3. Create ShoonyaAuthenticator class")
    print("   4. Test authentication with real credentials")