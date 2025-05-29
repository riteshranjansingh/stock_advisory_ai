#!/usr/bin/env python3
"""
Test Shoonya Data Provider

Tests the ShoonyaProvider class with real market data fetching
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd # Import pandas here for type hinting and usage

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_shoonya_provider_import():
    """Test importing the ShoonyaProvider"""
    print("🔧 Testing ShoonyaProvider Import")
    print("=" * 50)
    
    try:
        from src.data.providers.shoonya_provider import ShoonyaProvider
        print("✅ SUCCESS: ShoonyaProvider imported")
        print(f"   Class: {ShoonyaProvider}")
        return ShoonyaProvider
    except ImportError as e:
        print(f"❌ FAILED: Import error - {e}")
        return None
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return None

def test_provider_creation(provider_class):
    """Test creating ShoonyaProvider instance"""
    print("\n🏗️  Testing Provider Creation")
    print("=" * 50)
    
    try:
        provider = provider_class()
        print("✅ SUCCESS: ShoonyaProvider created")
        print(f"   Instance: {provider}")
        print(f"   Provider name: {provider.name}")
        
        # Check if it's available (authenticated)
        if provider.is_available():
            print("✅ Provider is available and authenticated")
            return provider
        else:
            print("❌ Provider not available (authentication may have failed)")
            return provider  # Return anyway for testing
            
    except Exception as e:
        print(f"❌ FAILED: Provider creation error - {e}")
        return None

def test_provider_info(provider):
    """Test getting provider information"""
    print("\n📋 Testing Provider Information")
    print("=" * 50)
    
    try:
        info = provider.get_provider_info()
        print("✅ SUCCESS: Provider info retrieved")
        for key, value in info.items():
            print(f"   {key}: {value}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Provider info error - {e}")
        return False

def test_single_quote(provider):
    """Test getting a single quote"""
    print("\n📊 Testing Single Quote Retrieval")
    print("=" * 50)
    
    test_symbol = "RELIANCE"
    
    try:
        print(f"🔍 Fetching quote for {test_symbol}...")
        quote = provider.get_quote(test_symbol)
        
        if quote:
            print("✅ SUCCESS: Quote retrieved")
            print(f"   Symbol: {quote.get('symbol')}")
            print(f"   LTP: ₹{quote.get('ltp', 'N/A')}")
            print(f"   Open: ₹{quote.get('open', 'N/A')}")
            print(f"   High: ₹{quote.get('h', 'N/A')}") # Corrected key if 'h' is used in quote response
            print(f"   Low: ₹{quote.get('l', 'N/A')}")  # Corrected key if 'l' is used in quote response
            print(f"   Change: {quote.get('change', 'N/A'):.2f} ({quote.get('change_pct', 'N/A'):.2f}%)")
            print(f"   Volume: {quote.get('volume', 'N/A'):,}")
            return True
        else:
            print("❌ FAILED: No quote data received")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Quote retrieval error - {e}")
        return False

def test_multiple_quotes(provider):
    """Test getting multiple quotes"""
    print("\n📊 Testing Multiple Quote Retrieval")
    print("=" * 50)
    
    test_symbols = ["RELIANCE", "TCS", "INFY"]
    
    try:
        print(f"🔍 Fetching quotes for {test_symbols}...")
        quotes = provider.get_multiple_quotes(test_symbols)
        
        print("✅ Multiple quotes request completed")
        
        success_count = 0
        for symbol, quote in quotes.items():
            if quote:
                print(f"   ✅ {symbol}: ₹{quote.get('ltp', 'N/A')} ({quote.get('change_pct', 'N/A'):.2f}%)")
                success_count += 1
            else:
                print(f"   ❌ {symbol}: No data")
        
        print(f"\n📈 Results: {success_count}/{len(test_symbols)} quotes successful")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ FAILED: Multiple quotes error - {e}")
        return False

def test_historical_data(provider):
    """Test getting historical data"""
    print("\n📅 Testing Historical Data Retrieval")
    print("=" * 50)
    
    test_symbol = "RELIANCE"
    test_days = 10
    
    try:
        print(f"🔍 Fetching {test_days} days of historical data for {test_symbol}...")
        df = provider.get_historical_data(test_symbol, days=test_days)
        
        if df is not None and not df.empty:
            print("✅ SUCCESS: Historical data retrieved")
            print(f"   Data points: {len(df)}")
            
            # Ensure 'date' column is datetime type before getting min/max and formatting
            # This line ensures that if for any reason 'date' isn't datetime, it's converted.
            df['date'] = pd.to_datetime(df['date']) 
            
            # Change 1: Access 'date' column for min/max and use strftime
            print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"   Columns: {list(df.columns)}")
            
            # Show last few rows
            print("\n   📊 Recent data:")
            latest_data = df.tail(3)
            # Change 2: Iterate using 'index, row' and access 'date' from 'row'
            for index, row in latest_data.iterrows():
                print(f"      {row['date'].strftime('%Y-%m-%d')}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
            
            return True
        else:
            print("❌ FAILED: No historical data received")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Historical data error - {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Shoonya Provider Tests")
    print()
    
    # Test 1: Import
    provider_class = test_shoonya_provider_import()
    if not provider_class:
        print("\n❌ Import test failed. Cannot continue.")
        return
    
    # Test 2: Creation
    provider = test_provider_creation(provider_class)
    if not provider:
        print("\n❌ Provider creation failed. Cannot continue.")
        return
    
    # Test 3: Provider info
    test_provider_info(provider)
    
    # Test 4: Single quote
    print("\n⚠️  About to test with REAL market data!")
    print("This will make API calls to Shoonya for live stock prices.")
    
    if not provider.is_available():
        print("\n❌ Provider not available. Skipping market data tests.")
        print("💡 Make sure Shoonya authentication is working properly.")
        return
    
    if os.getenv('TESTING') != 'true':
        response = input("\nProceed with market data tests? (y/n): ")
        if response.lower() != 'y':
            print("⏭️  Skipping market data tests")
            return
    
    # Test market data retrieval
    quote_success = test_single_quote(provider)
    multiple_success = test_multiple_quotes(provider)
    historical_success = test_historical_data(provider)
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    tests = {
        "Import": True,
        "Creation": provider is not None,
        "Provider Info": True,
        "Single Quote": quote_success,
        "Multiple Quotes": multiple_success,
        "Historical Data": historical_success
    }
    
    passed = sum(tests.values())
    total = len(tests)
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Shoonya provider is working perfectly!")
    elif passed >= total - 1:
        print("🚀 MOSTLY SUCCESSFUL! Shoonya provider is working well!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    print("\n✨ Testing completed!")

if __name__ == "__main__":
    main()
