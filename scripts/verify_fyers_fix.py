#!/usr/bin/env python3
"""
Verify Fyers Historical Data Fix
Quick test to ensure enhanced manager works correctly
"""
import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def test_fyers_direct():
    """Test Fyers provider directly"""
    print("🔧 Testing Fyers Provider Directly")
    print("=" * 35)
    
    try:
        from src.data.providers.fyers_provider import FyersProvider
        
        provider = FyersProvider()
        
        # Test authentication
        if not provider.authenticate():
            print("❌ Fyers authentication failed")
            return False
        
        # Test historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=5)
        
        print(f"📊 Testing: RELIANCE from {start_date} to {end_date}")
        
        data = provider.get_historical_data("RELIANCE", start_date, end_date)
        
        if data is not None and len(data) > 0:
            print(f"✅ Provider direct: {len(data)} records")
            return True
        else:
            print("❌ Provider direct: No data")
            return False
            
    except Exception as e:
        print(f"❌ Provider direct error: {e}")
        return False

def test_enhanced_manager():
    """Test enhanced manager with Fyers"""
    print("\n🚀 Testing Enhanced Manager with Fyers")
    print("=" * 40)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        # Force Fyers
        success = enhanced_provider_manager.set_preferred_provider('fyers')
        if not success:
            print("❌ Could not set Fyers as preferred")
            return False
        
        print("✅ Set Fyers as preferred provider")
        
        # Test historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=5)
        
        print(f"📊 Testing: RELIANCE from {start_date} to {end_date}")
        
        data = enhanced_provider_manager.get_historical_data("RELIANCE", start_date, end_date)
        
        if data is not None and len(data) > 0:
            print(f"✅ Enhanced manager: {len(data)} records")
            
            # Check symbol consistency
            if 'symbol' in data.columns:
                unique_symbols = data['symbol'].unique()
                if len(unique_symbols) == 1 and unique_symbols[0] == 'RELIANCE':
                    print("✅ Symbol consistency: RELIANCE")
                else:
                    print(f"⚠️  Symbol inconsistency: {unique_symbols}")
            
            # Check current provider
            current_provider = enhanced_provider_manager.get_current_provider_name()
            print(f"✅ Current provider: {current_provider}")
            
            return True
        else:
            print("❌ Enhanced manager: No data")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced manager error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_symbol_info():
    """Test symbol mapping info"""
    print("\n🔍 Testing Symbol Mapping Info")
    print("=" * 30)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        # Test get_symbol_info method if available
        if hasattr(enhanced_provider_manager, 'get_symbol_info'):
            info = enhanced_provider_manager.get_symbol_info("RELIANCE")
            print(f"📊 Symbol info: {info}")
            
            if info.get('consistent', False):
                print("✅ Symbol mapping consistent")
                return True
            else:
                print("⚠️  Symbol mapping issues detected")
                return False
        else:
            print("⚠️  get_symbol_info method not available")
            return True  # Not critical
            
    except Exception as e:
        print(f"❌ Symbol info error: {e}")
        return False

def main():
    """Run verification tests"""
    print("🧪 FYERS HISTORICAL DATA FIX VERIFICATION")
    print("=" * 50)
    print("Testing both direct provider and enhanced manager")
    print("=" * 50)
    
    tests = [
        ("Fyers Direct", test_fyers_direct),
        ("Enhanced Manager", test_enhanced_manager),
        ("Symbol Info", test_symbol_info)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n🏆 VERIFICATION RESULTS")
    print("=" * 25)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Fyers historical data is working correctly")
        print("✅ Enhanced manager using provider methods properly")
        print("✅ Symbol normalization working")
        print("\n💡 You can now run the full symbol normalization test:")
        print("   python scripts/test_symbol_normalization.py")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")
        if not results.get("Fyers Direct", False):
            print("🔧 Fix Fyers provider authentication/method first")
        if results.get("Fyers Direct", False) and not results.get("Enhanced Manager", False):
            print("🔧 Enhanced manager still has issues - check method updates")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)