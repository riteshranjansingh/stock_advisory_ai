#!/usr/bin/env python3
"""
Switch to Fyers Data Provider
Manual override to use Fyers as preferred provider
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def main():
    """Switch to Fyers provider"""
    print("🔄 Switching to Fyers Data Provider")
    print("=" * 40)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        # Switch to Fyers
        success = enhanced_provider_manager.set_preferred_provider('fyers')
        
        if success:
            print("✅ Successfully switched to Fyers!")
            print("📊 Fyers is now your preferred data provider")
            print("🔄 Automatic failsafe still active if Fyers fails")
            
            # Test connection
            current_provider = enhanced_provider_manager.get_active_provider()
            if current_provider and current_provider.name.lower() == 'fyers':
                print("🟢 Fyers connection verified")
                
                # Optional: Test with a quick quote
                stock_info = enhanced_provider_manager.get_stock_info('RELIANCE')
                if stock_info:
                    print("📈 Test quote successful - Fyers is working!")
                else:
                    print("⚠️  Fyers connected but test quote failed")
            else:
                print("⚠️  Switch successful but Fyers may not be healthy")
        else:
            print("❌ Failed to switch to Fyers")
            print("💡 Possible reasons:")
            print("   • Fyers not registered/authenticated")
            print("   • Network connectivity issues")
            print("   • Check logs for details")
            
    except ImportError as e:
        print("❌ Import error - enhanced provider manager not found")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error switching to Fyers: {e}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)