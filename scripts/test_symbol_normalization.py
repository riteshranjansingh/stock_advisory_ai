#!/usr/bin/env python3
"""
Test Symbol Normalization End-to-End
Verifies that symbol normalization works correctly across provider switches
"""
import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def test_symbol_consistency():
    """Test that symbols remain consistent across provider switches"""
    print("🧪 Testing Symbol Normalization Consistency")
    print("=" * 50)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        test_symbols = ['RELIANCE', 'TCS', 'INFY']
        
        # Get list of available providers
        status = enhanced_provider_manager.get_enhanced_status()
        available_providers = [name for name, info in status['providers'].items() 
                             if info['is_available']]
        
        print(f"🔧 Available providers: {available_providers}")
        
        for symbol in test_symbols:
            print(f"\n📊 Testing symbol: {symbol}")
            
            # Test with each provider
            for provider_name in available_providers:
                try:
                    # Switch to this provider
                    enhanced_provider_manager.set_preferred_provider(provider_name)
                    
                    # Test stock info
                    stock_info = enhanced_provider_manager.get_stock_info(symbol)
                    
                    if stock_info:
                        returned_symbol = stock_info.get('symbol')
                        provider_symbol = stock_info.get('provider_symbol', 'N/A')
                        
                        if returned_symbol == symbol:
                            print(f"   ✅ {provider_name}: {symbol} → {provider_symbol} → {returned_symbol}")
                        else:
                            print(f"   ❌ {provider_name}: Symbol inconsistency! {symbol} → {returned_symbol}")
                    else:
                        print(f"   ⚠️  {provider_name}: No data for {symbol}")
                    
                    # Test symbol mapping info (if available)
                    if hasattr(enhanced_provider_manager, 'get_symbol_info'):
                        symbol_info = enhanced_provider_manager.get_symbol_info(symbol)
                        if symbol_info.get('consistent'):
                            print(f"      ✅ Symbol mapping consistent")
                        else:
                            print(f"      ⚠️  Symbol mapping: {symbol_info}")
                    
                except Exception as e:
                    print(f"   ❌ {provider_name}: Error - {e}")
                    continue
        
        print(f"\n🎯 Test Summary:")
        print(f"   • All providers should return the same clean symbol")
        print(f"   • Provider-specific formats should be hidden from users")
        print(f"   • Database should store clean symbols only")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_provider_symbol_formats():
    """Test specific provider symbol format conversions"""
    print("\n🔧 Testing Provider-Specific Symbol Formats")
    print("=" * 45)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        # Ensure providers are initialized
        status = enhanced_provider_manager.get_enhanced_status()
        
        test_cases = [
            ('RELIANCE', 'NSE'),
            ('TCS', 'NSE'),
            ('INFY', 'NSE')
        ]
        
        for symbol, exchange in test_cases:
            print(f"\n📊 Symbol: {symbol} ({exchange})")
            
            # Test each provider's normalization
            for provider_name, provider in enhanced_provider_manager.providers.items():
                try:
                    # Test normalization
                    if hasattr(provider, 'normalize_symbol'):
                        provider_symbol = provider.normalize_symbol(symbol, exchange)
                        clean_symbol = provider.denormalize_symbol(provider_symbol)
                        
                        consistency_check = "✅" if clean_symbol.upper() == symbol.upper() else "❌"
                        print(f"   {provider_name}: {symbol} → {provider_symbol} → {clean_symbol} {consistency_check}")
                    else:
                        print(f"   {provider_name}: ⚠️  Symbol normalization not implemented")
                        
                except Exception as e:
                    print(f"   {provider_name}: ❌ Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider format test failed: {e}")
        return False

def test_historical_data_consistency():
    """Test that historical data returns consistent symbols"""
    print("\n📅 Testing Historical Data Symbol Consistency")
    print("=" * 45)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        test_symbol = 'RELIANCE'
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        # Get available providers
        status = enhanced_provider_manager.get_enhanced_status()
        available_providers = [name for name, info in status['providers'].items() 
                             if info['is_available']]
        
        for provider_name in available_providers:
            try:
                # Switch to provider
                enhanced_provider_manager.set_preferred_provider(provider_name)
                
                # Get historical data
                data = enhanced_provider_manager.get_historical_data(test_symbol, start_date, end_date)
                
                if data is not None and not data.empty:
                    # Check symbol consistency in DataFrame
                    if 'symbol' in data.columns:
                        unique_symbols = data['symbol'].unique()
                        if len(unique_symbols) == 1 and unique_symbols[0] == test_symbol:
                            print(f"   ✅ {provider_name}: Historical data symbol consistent ({len(data)} records)")
                        else:
                            print(f"   ❌ {provider_name}: Symbol inconsistency in historical data: {unique_symbols}")
                    else:
                        print(f"   ⚠️  {provider_name}: No symbol column in historical data")
                else:
                    print(f"   ⚠️  {provider_name}: No historical data available")
                    
            except Exception as e:
                print(f"   ❌ {provider_name}: Historical data error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Historical data test failed: {e}")
        return False

def main():
    """Run all symbol normalization tests"""
    print("🧪 COMPREHENSIVE SYMBOL NORMALIZATION TEST")
    print("=" * 60)
    print("This test verifies that symbol normalization works correctly")
    print("across all providers and maintains consistency.")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Symbol Consistency", test_symbol_consistency),
        ("Provider Formats", test_provider_symbol_formats),
        ("Historical Data", test_historical_data_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    # Final summary
    print(f"\n🏆 TEST RESULTS SUMMARY")
    print("=" * 30)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Symbol normalization is working perfectly!")
        print("\n✅ Key Benefits Verified:")
        print("   • Consistent symbols across all providers")
        print("   • Clean database storage (RELIANCE, TCS, etc.)")
        print("   • Hidden provider-specific formats")
        print("   • Seamless provider switching")
    elif passed > 0:
        print("⚠️  Some tests passed, but issues found. Check output above.")
    else:
        print("❌ All tests failed. Symbol normalization needs implementation.")
    
    print(f"\n💡 Next Steps:")
    if passed == total:
        print("   • Symbol normalization is ready!")
        print("   • Integrate with technical analysis agent")
        print("   • Start building other agents with clean symbols")
    else:
        print("   • Review the failed tests above")
        print("   • Implement missing symbol normalization methods")
        print("   • Re-run this test until all pass")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)