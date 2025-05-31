#!/usr/bin/env python3
"""
Reset Provider Health Status
Clears failure counts and health status for all providers
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def main():
    """Reset provider health status"""
    print("🔄 Resetting Provider Health Status")
    print("=" * 40)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        # Get current status before reset
        status_before = enhanced_provider_manager.get_enhanced_status()
        
        print("📊 Status Before Reset:")
        for provider_name, provider_info in status_before['providers'].items():
            health = provider_info['health']
            failures = provider_info['failure_count']
            print(f"   {provider_name}: {health} ({failures} failures)")
        
        # Reset all providers
        enhanced_provider_manager.reset_provider_health()
        
        print("\n🔄 Resetting...")
        print("   ✅ Cleared all failure counts")
        print("   ✅ Reset health status to unknown")
        print("   ✅ Reset recovery notification flags")
        
        # Perform fresh health check
        print("\n🏥 Performing fresh health check...")
        enhanced_provider_manager.startup_health_check()
        
        # Show status after reset
        status_after = enhanced_provider_manager.get_enhanced_status()
        
        print("\n📊 Status After Reset:")
        for provider_name, provider_info in status_after['providers'].items():
            health = provider_info['health']
            failures = provider_info['failure_count']
            available = "✅" if provider_info['is_available'] else "❌"
            print(f"   {provider_name}: {health} ({failures} failures) {available}")
        
        current_provider = status_after['current_provider']
        print(f"\n🎯 Current Provider: {current_provider}")
        print("\n✅ Provider reset complete!")
        print("💡 All providers have been given a fresh start")
        
        return True
        
    except ImportError as e:
        print("❌ Import error - enhanced provider manager not found")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error resetting providers: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)