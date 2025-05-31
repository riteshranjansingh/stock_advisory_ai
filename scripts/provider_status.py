#!/usr/bin/env python3
"""
Provider Status Tool
Shows comprehensive status of all data providers
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def format_health_status(health_str: str) -> str:
    """Format health status with emoji"""
    health_map = {
        'healthy': '🟢 Healthy',
        'degraded': '🟡 Degraded',
        'failed': '🔴 Failed',
        'recovering': '🟠 Recovering',
        'unknown': '⚪ Unknown'
    }
    return health_map.get(health_str.lower(), f'❓ {health_str}')

def format_time_ago(timestamp):
    """Format timestamp as time ago"""
    if not timestamp:
        return "Never"
    
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    now = datetime.now()
    if timestamp.tzinfo:
        now = now.replace(tzinfo=timestamp.tzinfo)
    
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"

def main():
    """Show comprehensive provider status"""
    print("📊 Data Provider Status Dashboard")
    print("=" * 50)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        from config.provider_config import provider_config
        
        # Get comprehensive status (this will trigger auto-initialization)
        status = enhanced_provider_manager.get_enhanced_status()
        
        # Check if initialization failed
        if status.get('initialization_failed'):
            print("⚠️  Provider initialization failed")
            print("💡 This might happen if:")
            print("   • No broker credentials are configured")
            print("   • Network connectivity issues")
            print("   • Import errors in provider modules")
            print(f"\n🔧 Try running: python scripts/setup_providers.py")
            return False
        
        # Current provider info
        print(f"🎯 Current Provider: {status['current_provider'] or 'None'}")
        print(f"⭐ Preferred Provider: {status['preferred_provider'] or 'Auto (Default)'}")
        print(f"🔄 Failover Enabled: {'✅ Yes' if status['failover_enabled'] else '❌ No'}")
        print(f"🏥 Health Monitoring: {'✅ Yes' if status['health_monitoring'] else '❌ No'}")
        print(f"📈 Total Providers: {status['total_providers']}")
        
        print(f"\n📋 Provider Priority Order:")
        for i, provider_name in enumerate(status['provider_order'], 1):
            current_marker = " 👈 CURRENT" if provider_name == status['current_provider'] else ""
            preferred_marker = " ⭐ PREFERRED" if provider_name == status['preferred_provider'] else ""
            print(f"   {i}. {provider_name.title()}{current_marker}{preferred_marker}")
        
        print(f"\n🏥 Provider Health Status:")
        print("-" * 50)
        
        for provider_name, provider_info in status['providers'].items():
            print(f"\n📡 {provider_name.upper()}")
            print(f"   Status: {format_health_status(provider_info['health'])}")
            print(f"   Available: {'✅ Yes' if provider_info['is_available'] else '❌ No'}")
            print(f"   Failures: {provider_info['failure_count']}")
            print(f"   Requests Today: {provider_info['requests_today']}/{provider_info['daily_limit']}")
            
            if provider_info['last_failure']:
                print(f"   Last Failure: {format_time_ago(provider_info['last_failure'])}")
            
            if provider_info.get('last_request_time'):
                print(f"   Last Request: {format_time_ago(provider_info['last_request_time'])}")
            
            # Provider-specific info
            if hasattr(enhanced_provider_manager.providers.get(provider_name), 'get_provider_info'):
                try:
                    provider_details = enhanced_provider_manager.providers[provider_name].get_provider_info()
                    if 'authenticated' in provider_details:
                        auth_status = "✅ Yes" if provider_details['authenticated'] else "❌ No"
                        print(f"   Authenticated: {auth_status}")
                except:
                    pass
        
        print(f"\n⚙️  Configuration Details:")
        print("-" * 30)
        print(f"   Default Provider: {provider_config.get_default_provider()}")
        print(f"   Retry Attempts: {provider_config.get_retry_attempts()}")
        print(f"   Stay Switched: {'Yes' if provider_config.should_stay_switched() else 'No'}")
        
        print(f"\n🔧 Available Commands:")
        print("-" * 20)
        print("   switch_provider_fyers    - Switch to Fyers")
        print("   switch_provider_shoonya  - Switch to Shoonya")  
        print("   switch_provider_mstock   - Switch to MStock")
        print("   switch_provider_upstox   - Switch to Upstox (future)")
        print("   provider_status          - Show this status")
        print("   reset_providers          - Reset all provider health")
        
        return True
        
    except ImportError as e:
        print("❌ Import error - enhanced provider manager not found")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error getting provider status: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)