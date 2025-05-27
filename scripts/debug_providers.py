"""
Debug Providers Script  
Simple test to debug provider issues
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.providers.sample_provider import SampleDataProvider
from src.data.providers.provider_manager import provider_manager

def test_sample_provider_directly():
    """Test sample provider directly"""
    print("🔧 Testing Sample Provider Directly")
    print("=" * 35)
    
    # Create sample provider
    sample_provider = SampleDataProvider()
    print(f"Provider Status: {sample_provider.status}")
    print(f"Is Available: {sample_provider.is_available()}")
    print(f"Check Rate Limit: {sample_provider.check_rate_limit()}")
    
    # Test stock info
    print("\n📊 Testing Stock Info:")
    try:
        reliance_info = sample_provider.get_stock_info('RELIANCE')
        print(f"RELIANCE: {reliance_info}")
    except Exception as e:
        print(f"RELIANCE Error: {e}")
    
    try:
        tcs_info = sample_provider.get_stock_info('TCS')
        print(f"TCS: {tcs_info}")
    except Exception as e:
        print(f"TCS Error: {e}")
    
    # Test historical data
    print("\n📈 Testing Historical Data:")
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        hist_data = sample_provider.get_historical_data('RELIANCE', start_date, end_date)
        print(f"Historical Data Length: {len(hist_data) if hist_data is not None else 0}")
        if hist_data is not None and len(hist_data) > 0:
            print(f"Date Range: {hist_data['date'].min()} to {hist_data['date'].max()}")
    except Exception as e:
        print(f"Historical Data Error: {e}")
    
    # Test real-time data
    print("\n⚡ Testing Real-time Data:")
    try:
        rt_data = sample_provider.get_real_time_data(['RELIANCE', 'TCS'])
        print(f"Real-time Data: {rt_data}")
    except Exception as e:
        print(f"Real-time Data Error: {e}")

def test_provider_manager():
    """Test provider manager"""
    print("\n🔧 Testing Provider Manager")
    print("=" * 28)
    
    # Clear any existing providers
    provider_manager.providers.clear()
    provider_manager.provider_order.clear()
    provider_manager.current_provider = None
    
    # Register sample provider
    sample_provider = SampleDataProvider()
    success = provider_manager.register_provider(sample_provider)
    print(f"Registration Success: {success}")
    
    # Check status
    status = provider_manager.get_provider_status()
    print(f"Status: {status}")
    
    # Test operations
    print("\n📊 Testing via Provider Manager:")
    
    # Test stock info
    reliance_info = provider_manager.get_stock_info('RELIANCE')
    print(f"RELIANCE Info: {reliance_info}")
    
    tcs_info = provider_manager.get_stock_info('TCS')
    print(f"TCS Info: {tcs_info}")

def main():
    """Main debug function"""
    print("🐛 Provider System Debug")
    print("=" * 25)
    
    # Test sample provider directly
    test_sample_provider_directly()
    
    # Test provider manager
    test_provider_manager()

if __name__ == "__main__":
    main()