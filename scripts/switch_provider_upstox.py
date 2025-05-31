#!/usr/bin/env python3
"""
Switch to Upstox Data Provider (Future Implementation)
Manual override to use Upstox as preferred provider
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def main():
    """Switch to Upstox provider"""
    print("🔄 Switching to Upstox Data Provider")
    print("=" * 40)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        # Check if Upstox is registered
        status = enhanced_provider_manager.get_enhanced_status()
        if 'upstox' not in status['providers']:
            print("❌ Upstox provider not implemented yet")
            print("💡 Future feature - will be available in next update")
            print("🔄 Current providers: Fyers, Shoonya, MStock")
            return False
        
        # Switch to Upstox
        success = enhanced_provider_manager.set_preferred_provider('upstox')
        
        if success:
            print("✅ Successfully switched to Upstox!")
            print("📊 Upstox is now your preferred data provider")
            print("🔄 Automatic failsafe still active if Upstox fails")
            
            # Test connection
            current_provider = enhanced_provider_manager.get_active_provider()
            if current_provider and current_provider.name.lower() == 'upstox':
                print("🟢 Upstox connection verified")
                
                # Optional: Test with a quick quote
                stock_info = enhanced_provider_manager.get_stock_info('RELIANCE')
                if stock_info:
                    print("📈 Test quote successful - Upstox is working!")
                else:
                    print("⚠️  Upstox connected but test quote failed")
            else:
                print("⚠️  Switch successful but Upstox may not be healthy")
        else:
            print("❌ Failed to switch to Upstox")
            print("💡 Possible reasons:")
            print("   • Upstox not registered/authenticated")
            print("   • Network connectivity issues")
            print("   • Check logs for details")
            
    except ImportError as e:
        print("❌ Import error - enhanced provider manager not found")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error switching to Upstox: {e}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)