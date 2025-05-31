#!/usr/bin/env python3
"""
Test Auto-Registration Feature
Quick test to verify that auto-registration is working
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def test_auto_registration():
    """Test that providers auto-register when first accessed"""
    print("🧪 Testing Auto-Registration Feature")
    print("=" * 40)
    
    try:
        # Import the enhanced provider manager
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        print("✅ Enhanced provider manager imported")
        
        # This should trigger auto-registration
        print("🔧 Triggering auto-registration by calling get_enhanced_status()...")
        status = enhanced_provider_manager.get_enhanced_status()
        
        # Check results
        if status.get('initialization_failed'):
            print("❌ Auto-registration failed")
            print("💡 Possible reasons:")
            print("   • Missing provider modules")
            print("   • Import errors")
            print("   • Broker authentication issues (this is normal)")
            return False
        
        print(f"✅ Auto-registration successful!")
        print(f"📊 Registered {status['total_providers']} providers")
        print(f"🎯 Current provider: {status['current_provider']}")
        
        print(f"\n🏥 Provider Status:")
        for provider_name, provider_info in status['providers'].items():
            health = provider_info['health']
            available = "✅" if provider_info['is_available'] else "❌"
            print(f"   {provider_name}: {health} {available}")
        
        # Test a quick operation
        print(f"\n📊 Testing quick stock info lookup...")
        stock_info = enhanced_provider_manager.get_stock_info('RELIANCE')
        
        if stock_info:
            current_provider = enhanced_provider_manager.get_current_provider_name()
            print(f"   ✅ Success via {current_provider}")
            print(f"   📈 Got info for: {stock_info.get('name', 'RELIANCE')}")
        else:
            print(f"   ⚠️  No stock info available (providers may need authentication)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auto_registration()
    
    if success:
        print("\n🎉 Auto-registration test passed!")
        print("💡 Now try: python scripts/provider_status.py")
    else:
        print("\n❌ Auto-registration test failed")
        print("💡 Check the error messages above")
    
    sys.exit(0 if success else 1)