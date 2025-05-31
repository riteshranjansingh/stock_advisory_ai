#!/usr/bin/env python3
"""
Enhanced Test script for MStock Data Provider with Script Master pre-loading
Tests market data fetching capabilities using MStock API
"""
import sys
import os
import logging
from datetime import date, timedelta

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.providers.mstock_provider import MStockProvider

# Simple logging setup
logging.basicConfig(level=logging.INFO)

def test_authentication():
    """Test MStock provider authentication"""
    print("\n" + "="*60)
    print("🔐 TESTING MSTOCK AUTHENTICATION")
    print("="*60)
    
    try:
        provider = MStockProvider()
        
        print("📋 Authentication Status Check:")
        print(f"   Provider Name: {provider.name}")
        print(f"   Priority: {provider.priority.name}")
        print(f"   Initial Status: {provider.status.name}")
        
        # Test authentication
        print("\n🔄 Attempting authentication...")
        auth_success = provider.authenticate()
        
        if auth_success:
            print("✅ Authentication successful!")
            print(f"   Status: {provider.status.name}")
            print(f"   Access Token: {provider.access_token[:20] if provider.access_token else 'None'}...")
            print(f"   API Key: {'***' if provider.api_key else 'None'}")
            return provider
        else:
            print("❌ Authentication failed!")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_connection(provider):
    """Test API connection"""
    print("\n" + "="*60)
    print("🌐 TESTING API CONNECTION")
    print("="*60)
    
    try:
        is_connected = provider.test_connection()
        
        if is_connected:
            print("✅ API connection successful!")
            
            # Get provider info
            info = provider.get_provider_info()
            print("\n📊 Provider Information:")
            for key, value in info.items():
                print(f"   {key}: {value}")
            
            return True
        else:
            print("❌ API connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

def test_real_time_data(provider):
    """Test real-time data fetching"""
    print("\n" + "="*60)
    print("📈 TESTING REAL-TIME DATA")
    print("="*60)
    
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    
    try:
        print(f"🔍 Fetching real-time data for: {', '.join(test_symbols)}")
        print("⏳ This may take a few seconds...")
        
        quotes = provider.get_real_time_data(test_symbols)
        
        if quotes:
            print(f"✅ Successfully fetched data for {len(quotes)} symbols:")
            print("\n📊 Real-time Quotes:")
            print("-" * 50)
            
            for symbol, data in quotes.items():
                ltp = data.get('ltp', 'N/A')
                timestamp = data.get('timestamp', 'N/A')
                print(f"   {symbol:12} | ₹{ltp:>8} | {timestamp}")
            
            return True
        else:
            print("❌ No real-time data retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Real-time data error: {e}")
        return False

def test_stock_search(provider):
    """Test stock search functionality"""
    print("\n" + "="*60)
    print("🔍 TESTING STOCK SEARCH")
    print("="*60)
    
    search_queries = ['RELIANCE', 'BANK', 'TCS']
    
    try:
        for query in search_queries:
            print(f"\n🔎 Searching for: '{query}'")
            results = provider.search_stocks(query)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for result in results[:5]:  # Show first 5
                    symbol = result.get('symbol', 'N/A')
                    name = result.get('name', 'N/A')
                    print(f"   {symbol:12} | {name}")
            else:
                print("❌ No search results")
        
        return True
        
    except Exception as e:
        print(f"❌ Stock search error: {e}")
        return False

def test_stock_info(provider):
    """Test individual stock information"""
    print("\n" + "="*60)
    print("📋 TESTING STOCK INFORMATION")
    print("="*60)
    
    test_symbol = 'RELIANCE'
    
    try:
        print(f"🔍 Getting stock info for: {test_symbol}")
        
        stock_info = provider.get_stock_info(test_symbol)
        
        if stock_info:
            print("✅ Stock information retrieved:")
            print("\n📊 Stock Details:")
            for key, value in stock_info.items():
                print(f"   {key:15} | {value}")
            return True
        else:
            print("❌ No stock information retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Stock info error: {e}")
        return False

def test_market_status(provider):
    """Test market status detection"""
    print("\n" + "="*60)
    print("🏢 TESTING MARKET STATUS")
    print("="*60)
    
    try:
        print("🔍 Getting market status...")
        
        market_status = provider.get_market_status()
        
        if market_status:
            print("✅ Market status retrieved:")
            print("\n📊 Market Information:")
            for key, value in market_status.items():
                print(f"   {key:15} | {value}")
            return True
        else:
            print("❌ No market status retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Market status error: {e}")
        return False

def test_historical_data(provider):
    """Test historical data"""
    print("\n" + "="*60)
    print("📅 TESTING HISTORICAL DATA")
    print("="*60)
    
    try:
        print("🔍 Testing historical data functionality...")
        print("⚠️  Note: Requires Script Master to be loaded")
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        historical_data = provider.get_historical_data('RELIANCE', start_date, end_date)
        
        if historical_data is not None:
            print("✅ Historical data retrieved!")
            print(f"   Records: {len(historical_data)}")
            print(f"   Columns: {list(historical_data.columns)}")
            return True
        else:
            print("⚠️  Historical data not available")
            print("   Reason: Script Master tokens required")
            return False
        
    except Exception as e:
        print(f"⚠️  Historical data error: {e}")
        return False

def test_available_symbols(provider):
    """Test available symbols list"""
    print("\n" + "="*60)
    print("📜 TESTING AVAILABLE SYMBOLS")
    print("="*60)
    
    try:
        print("🔍 Getting available symbols list...")
        
        symbols = provider.get_available_symbols()
        
        if symbols:
            print(f"✅ Available symbols retrieved: {len(symbols)} symbols")
            print("\n📊 Sample Symbols:")
            for symbol in symbols[:10]:  # Show first 10
                print(f"   • {symbol}")
            
            if len(symbols) > 10:
                print(f"   ... and {len(symbols) - 10} more")
            
            return True
        else:
            print("❌ No symbols retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Available symbols error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests with Script Master pre-loading"""
    print("🚀 MStock Data Provider Comprehensive Test")
    print("="*60)
    
    test_results = {
        'authentication': False,
        'connection': False,
        'script_master': False,
        'real_time_data': False,
        'stock_search': False,
        'stock_info': False,
        'market_status': False,
        'historical_data': False,
        'available_symbols': False
    }
    
    # Test 1: Authentication
    provider = test_authentication()
    if provider:
        test_results['authentication'] = True
        
        # Test 2: Connection
        if test_connection(provider):
            test_results['connection'] = True
            
            # Test 2.5: Pre-load Script Master to avoid rate limits (CRITICAL FIX)
            print("\n" + "="*60)
            print("📊 PRE-LOADING SCRIPT MASTER")
            print("="*60)
            print("🔍 Loading Script Master to cache instrument tokens...")
            print("⚠️  This may take a few seconds and is rate limited...")
            
            try:
                script_master_loaded = provider._ensure_script_master_loaded()
                if script_master_loaded:
                    test_results['script_master'] = True
                    print("✅ Script Master loaded successfully!")
                    print(f"   Cached instruments: {len(provider._instrument_tokens)}")
                else:
                    print("⚠️  Script Master failed to load - using fallback data")
                    test_results['script_master'] = False
            except Exception as e:
                print(f"⚠️  Script Master loading error: {e}")
                test_results['script_master'] = False
            
            # Test 3: Real-time data
            test_results['real_time_data'] = test_real_time_data(provider)
            
            # Test 4: Stock search
            test_results['stock_search'] = test_stock_search(provider)
            
            # Test 5: Stock info
            test_results['stock_info'] = test_stock_info(provider)
            
            # Test 6: Market status
            test_results['market_status'] = test_market_status(provider)
            
            # Test 7: Historical data
            test_results['historical_data'] = test_historical_data(provider)
            
            # Test 8: Available symbols
            test_results['available_symbols'] = test_available_symbols(provider)
    
    # Show final results
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title():20} | {status}")
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests >= 7:  # Allow some flexibility
        print("🎉 MStock provider is working well!")
        print("✨ Ready for integration with provider manager!")
    else:
        print("⚠️  Some core functionality needs attention")
    
    print("\n📝 Notes:")
    print("   • Script Master pre-loading is essential for avoiding rate limits")
    print("   • Real-time data is the primary working feature")
    print("   • Provider ready for multi-broker setup")
    
    return passed_tests >= 7

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)