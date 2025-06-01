#!/usr/bin/env python3
"""
Fyers Historical Data Diagnostic Script
Debug why historical data is failing while stock info works
"""
import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def test_fyers_authentication():
    """Test if Fyers authentication is working"""
    print("🔐 Testing Fyers Authentication")
    print("=" * 35)
    
    try:
        from src.auth.fyers_auth import FyersAuthenticator
        
        # Create authenticator
        auth = FyersAuthenticator()
        
        # Check if token exists and is valid
        print("1. Checking stored token...")
        if auth.load_existing_token():
            print("   ✅ Found stored token")
            
            if auth.is_token_valid():
                print("   ✅ Token is valid (not expired)")
            else:
                print("   ⚠️  Token appears expired")
                
            # Test token with API call
            print("   🧪 Testing token with API call...")
            if auth.test_token():
                print("   ✅ Token works with API")
                return True
            else:
                print("   ❌ Token fails API test")
                return False
        else:
            print("   ❌ No stored token found")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False

def test_fyers_symbol_formats():
    """Test different symbol formats with Fyers"""
    print("\n🔤 Testing Fyers Symbol Formats")
    print("=" * 35)
    
    try:
        from src.data.providers.fyers_provider import FyersProvider
        
        # Create provider
        provider = FyersProvider()
        
        # Test if provider is authenticated
        if not provider.authenticate():
            print("❌ Provider authentication failed")
            return False
        
        test_symbols = [
            "RELIANCE",
            "NSE:RELIANCE-EQ",
            "NSE:RELIANCE",
            "RELIANCE-EQ"
        ]
        
        print("📊 Testing stock info with different formats:")
        for symbol in test_symbols:
            try:
                result = provider.get_stock_info(symbol)
                if result:
                    print(f"   ✅ {symbol}: Success")
                else:
                    print(f"   ❌ {symbol}: No data")
            except Exception as e:
                print(f"   ❌ {symbol}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Symbol format test failed: {e}")
        return False

def test_fyers_historical_formats():
    """Test historical data with different symbol formats"""
    print("\n📅 Testing Fyers Historical Data Formats")
    print("=" * 40)
    
    try:
        from src.data.providers.fyers_provider import FyersProvider
        
        # Create provider
        provider = FyersProvider()
        
        # Test if provider is authenticated
        if not provider.authenticate():
            print("❌ Provider authentication failed")
            return False
        
        # Get authenticated client directly
        fyers_client = provider.get_authenticated_client()
        if not fyers_client:
            print("❌ Could not get Fyers client")
            return False
        
        # Test different symbol formats
        test_symbols = [
            "RELIANCE",
            "NSE:RELIANCE-EQ", 
            "NSE:RELIANCE",
            "RELIANCE-EQ"
        ]
        
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        # Convert to timestamps for Fyers
        import time
        start_timestamp = str(int(time.mktime(start_date.timetuple())))
        end_timestamp = str(int(time.mktime(end_date.timetuple())))
        
        print(f"📊 Testing historical data ({start_date} to {end_date}):")
        
        for symbol in test_symbols:
            try:
                print(f"\n   🔍 Testing: {symbol}")
                
                # Test with Fyers history API directly
                data_params = {
                    'symbol': symbol,
                    'resolution': 'D',
                    'date_format': '0',
                    'range_from': start_timestamp,
                    'range_to': end_timestamp,
                    'cont_flag': '1'
                }
                
                print(f"      API params: {data_params}")
                
                response = fyers_client.history(data=data_params)
                print(f"      Response status: {response.get('s', 'unknown')}")
                
                if response.get('s') == 'ok':
                    candles = response.get('candles', [])
                    print(f"      ✅ Success: {len(candles)} candles")
                    if candles:
                        print(f"      📊 Sample data: {candles[0]}")
                else:
                    print(f"      ❌ Failed: {response.get('message', 'Unknown error')}")
                    print(f"      Full response: {response}")
                    
            except Exception as e:
                print(f"      ❌ Exception: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Historical data test failed: {e}")
        return False

def test_fyers_provider_methods():
    """Test the provider's historical data method specifically"""
    print("\n🔧 Testing Fyers Provider Historical Method")
    print("=" * 42)
    
    try:
        from src.data.providers.fyers_provider import FyersProvider
        
        # Create provider
        provider = FyersProvider()
        
        # Test historical data method
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        test_symbols = ["RELIANCE", "TCS"]
        
        for symbol in test_symbols:
            print(f"\n📊 Testing provider.get_historical_data('{symbol}'):")
            
            try:
                # Test the provider method directly
                data = provider.get_historical_data(symbol, start_date, end_date)
                
                if data is not None and len(data) > 0:
                    print(f"   ✅ Success: {len(data)} records")
                    print(f"   📈 Columns: {list(data.columns)}")
                    print(f"   📊 Sample: {data.iloc[0].to_dict()}")
                else:
                    print(f"   ❌ No data returned")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Provider method test failed: {e}")
        return False

def test_fyers_normalization():
    """Test symbol normalization specifically"""
    print("\n🔄 Testing Fyers Symbol Normalization")
    print("=" * 38)
    
    try:
        from src.data.providers.fyers_provider import FyersProvider
        
        # Create provider
        provider = FyersProvider()
        
        test_symbols = ["RELIANCE", "TCS", "INFY"]
        
        for symbol in test_symbols:
            try:
                print(f"\n📊 Testing normalization for: {symbol}")
                
                # Test normalize_symbol method
                if hasattr(provider, 'normalize_symbol'):
                    normalized = provider.normalize_symbol(symbol)
                    print(f"   🔄 Normalized: {symbol} → {normalized}")
                    
                    # Test denormalize
                    if hasattr(provider, 'denormalize_symbol'):
                        denormalized = provider.denormalize_symbol(normalized)
                        print(f"   🔙 Denormalized: {normalized} → {denormalized}")
                        
                        if denormalized.upper() == symbol.upper():
                            print(f"   ✅ Round-trip successful")
                        else:
                            print(f"   ❌ Round-trip failed")
                    else:
                        print(f"   ⚠️  No denormalize_symbol method")
                        
                    # Test with stock info
                    print(f"   🧪 Testing stock info with normalized symbol...")
                    stock_info = provider.get_stock_info(normalized)
                    if stock_info:
                        print(f"   ✅ Stock info works with normalized symbol")
                    else:
                        print(f"   ❌ Stock info fails with normalized symbol")
                        
                else:
                    print(f"   ⚠️  No normalize_symbol method found")
                    
            except Exception as e:
                print(f"   ❌ Error testing {symbol}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Normalization test failed: {e}")
        return False

def main():
    """Run comprehensive Fyers diagnostic"""
    print("🔍 FYERS HISTORICAL DATA DIAGNOSTIC")
    print("=" * 50)
    print("This will help identify why historical data is failing")
    print("=" * 50)
    
    # Run all diagnostic tests
    tests = [
        ("Authentication", test_fyers_authentication),
        ("Symbol Formats", test_fyers_symbol_formats), 
        ("Historical Formats", test_fyers_historical_formats),
        ("Provider Methods", test_fyers_provider_methods),
        ("Symbol Normalization", test_fyers_normalization)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            result = test_func()
            # Ensure result is boolean
            if isinstance(result, tuple):
                result = result[0]
            results[test_name] = bool(result)
            print(f"📊 {test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            print(f"📊 {test_name}: ❌ ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n🏆 DIAGNOSTIC SUMMARY")
    print("=" * 25)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 20)
    
    if not results.get("Authentication", False):
        print("🔐 Fix Fyers authentication first")
        print("   • Check credentials in .env file")
        print("   • Re-run authentication script")
        
    if results.get("Authentication", False) and not results.get("Historical Formats", False):
        print("📅 Historical data API issue detected")
        print("   • Symbol format might be different for historical API")
        print("   • Try different date ranges")
        print("   • Check Fyers API documentation")
        
    if results.get("Authentication", False) and results.get("Symbol Formats", False):
        print("🔄 Provider method issue")
        print("   • Check symbol normalization implementation")
        print("   • Verify API parameter format")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)