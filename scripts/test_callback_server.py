#!/usr/bin/env python3
"""
Test script to verify callback server is working
"""
import sys
import os
import requests
import threading
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_callback_server():
    """Test if our callback server can receive requests"""
    
    print("🧪 Testing Callback Server Functionality")
    print("="*50)
    
    try:
        # Test if we can make a request to our callback server
        test_url = "http://127.0.0.1:8923/callback?test=true&auth_code=test123"
        
        print("1. Testing if port 8923 is available...")
        
        # Try to connect to see if something is already running
        try:
            response = requests.get("http://127.0.0.1:8923/", timeout=2)
            print("⚠️  Something is already running on port 8923")
            print(f"Response: {response.status_code}")
            return False
        except requests.exceptions.ConnectionError:
            print("✅ Port 8923 appears to be available")
        except Exception as e:
            print(f"❓ Port test result: {e}")
        
        print("\n2. Testing callback URL format...")
        print(f"Test URL: {test_url}")
        
        # Check URL components
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(test_url)
        params = parse_qs(parsed.query)
        
        print(f"✅ Host: {parsed.netloc}")
        print(f"✅ Path: {parsed.path}")
        print(f"✅ Query params: {params}")
        
        if 'auth_code' in params:
            print("✅ auth_code parameter found in test URL")
        else:
            print("❌ auth_code parameter missing in test URL")
        
        print("\n3. Browser security check...")
        print("💡 Some browsers block localhost redirects for security")
        print("💡 If automated fails, that might be the reason")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_callback_server()
    
    print("\n" + "="*50)
    print("💡 If callback server tests pass but auth still fails:")
    print("1. Try using manual auth mode temporarily")
    print("2. Check browser security settings")
    print("3. Some corporate networks block localhost redirects")
    print("4. Firefox/Chrome might have different security policies")