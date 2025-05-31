#!/usr/bin/env python3
"""
Setup Enhanced Provider System
Initialize and configure all data providers with intelligent failover
"""
import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def setup_enhanced_provider_system():
    """Setup the complete enhanced provider system"""
    
    print("🚀 Setting Up Enhanced Provider System")
    print("=" * 50)
    
    try:
        # Import all required components
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        from src.data.providers.fyers_provider import FyersProvider
        from src.data.providers.shoonya_provider import ShoonyaProvider
        from src.data.providers.mstock_provider import MStockProvider
        from src.data.providers.sample_provider import SampleDataProvider
        from config.provider_config import provider_config
        
        print("✅ All imports successful")
        
        # Step 1: Register providers in priority order
        print("\n📡 Registering Data Providers...")
        print("-" * 30)
        
        providers_to_register = [
            ("Fyers", FyersProvider),
            ("Shoonya", ShoonyaProvider), 
            ("MStock", MStockProvider),
            ("Sample", SampleDataProvider)  # Always-available fallback
        ]
        
        registered_count = 0
        
        for provider_name, provider_class in providers_to_register:
            try:
                print(f"🔧 Registering {provider_name}...")
                
                # Create provider instance
                provider = provider_class()
                
                # Register with manager (authentication handled internally)
                success = enhanced_provider_manager.register_provider(provider)
                
                if success:
                    print(f"   ✅ {provider_name} registered successfully")
                    registered_count += 1
                else:
                    print(f"   ⚠️  {provider_name} registration failed (may need authentication)")
                    
            except Exception as e:
                print(f"   ❌ {provider_name} error: {e}")
                continue
        
        print(f"\n📊 Registration Summary: {registered_count}/{len(providers_to_register)} providers registered")
        
        # Step 2: Perform startup health check
        print("\n🏥 Performing Startup Health Check...")
        print("-" * 35)
        
        enhanced_provider_manager.startup_health_check()
        
        # Step 3: Show system status
        print("\n📋 System Status:")
        print("-" * 15)
        
        status = enhanced_provider_manager.get_enhanced_status()
        
        print(f"🎯 Current Provider: {status['current_provider']}")
        print(f"📈 Total Providers: {status['total_providers']}")
        print(f"🔄 Failover: {'Enabled' if status['failover_enabled'] else 'Disabled'}")
        print(f"🏥 Health Monitoring: {'Enabled' if status['health_monitoring'] else 'Disabled'}")
        
        print("\n🏥 Provider Health:")
        for provider_name, provider_info in status['providers'].items():
            health = provider_info['health']
            available = "✅" if provider_info['is_available'] else "❌"
            print(f"   {provider_name}: {health} {available}")
        
        # Step 4: Test basic functionality
        print("\n🧪 Testing Basic Functionality...")
        print("-" * 30)
        
        # Test stock info
        test_symbol = 'RELIANCE'
        print(f"📊 Testing stock info for {test_symbol}...")
        
        stock_info = enhanced_provider_manager.get_stock_info(test_symbol)
        if stock_info:
            current_provider = enhanced_provider_manager.get_current_provider_name()
            print(f"   ✅ Success via {current_provider}")
            print(f"   📈 {stock_info.get('name', test_symbol)}")
        else:
            print(f"   ❌ Failed to get stock info")
        
        # Test historical data
        print(f"\n📅 Testing historical data for {test_symbol}...")
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        historical_data = enhanced_provider_manager.get_historical_data(
            test_symbol, start_date, end_date
        )
        
        if historical_data is not None and len(historical_data) > 0:
            current_provider = enhanced_provider_manager.get_current_provider_name()
            print(f"   ✅ Success via {current_provider}")
            print(f"   📊 {len(historical_data)} records retrieved")
        else:
            print(f"   ❌ Failed to get historical data")
        
        # Step 5: Show CLI commands
        print("\n🔧 Available CLI Commands:")
        print("-" * 25)
        print("   python scripts/switch_provider_fyers.py")
        print("   python scripts/switch_provider_shoonya.py")
        print("   python scripts/switch_provider_mstock.py")
        print("   python scripts/provider_status.py")
        print("   python scripts/reset_providers.py")
        
        print("\n🎉 Enhanced Provider System Setup Complete!")
        print("💡 The system will automatically handle failover between providers")
        print("🎯 Use CLI commands above to manually switch providers when needed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all provider files are in place")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_provider_switching():
    """Test manual provider switching functionality"""
    
    print("\n🔄 Testing Provider Switching")
    print("=" * 30)
    
    try:
        from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
        
        # Get initial status
        initial_status = enhanced_provider_manager.get_enhanced_status()
        initial_provider = initial_status['current_provider']
        
        print(f"🎯 Starting with: {initial_provider}")
        
        # Test switching to each available provider
        available_providers = [name for name, info in initial_status['providers'].items() 
                             if info['is_available']]
        
        for provider_name in available_providers:
            if provider_name != initial_provider:
                print(f"\n🔄 Switching to {provider_name}...")
                
                success = enhanced_provider_manager.set_preferred_provider(provider_name)
                
                if success:
                    current = enhanced_provider_manager.get_current_provider_name()
                    if current == provider_name:
                        print(f"   ✅ Successfully switched to {provider_name}")
                    else:
                        print(f"   ⚠️  Switch attempted but current is {current}")
                else:
                    print(f"   ❌ Failed to switch to {provider_name}")
        
        # Switch back to original
        if initial_provider:
            print(f"\n🔄 Switching back to {initial_provider}...")
            enhanced_provider_manager.set_preferred_provider(initial_provider)
            print(f"   ✅ Restored to {initial_provider}")
        
        print("\n✅ Provider switching test complete!")
        
    except Exception as e:
        print(f"❌ Provider switching test failed: {e}")

def show_integration_example():
    """Show how to integrate with existing components"""
    
    print("\n🔗 Integration Example")
    print("=" * 20)
    
    example_code = """
# Example: Integrating with Technical Analysis Agent

from src.data.providers.enhanced_provider_manager import enhanced_provider_manager
from src.agents.data_agents.technical_agent import TechnicalAnalysisAgent
from datetime import date, timedelta

def analyze_stock_with_fallback(symbol: str):
    '''Analyze stock with automatic provider failover'''
    
    # Get historical data with intelligent fallback
    end_date = date.today()
    start_date = end_date - timedelta(days=200)
    
    price_data = enhanced_provider_manager.get_historical_data(
        symbol, start_date, end_date
    )
    
    if price_data is None:
        print(f"❌ No data available for {symbol}")
        return None
    
    # Use technical analysis agent
    tech_agent = TechnicalAnalysisAgent()
    analysis = tech_agent.analyze(symbol, {'price_data': price_data})
    
    current_provider = enhanced_provider_manager.get_current_provider_name()
    print(f"📊 Analysis completed using {current_provider}")
    
    return analysis

# Example: Custom provider selection for specific task
def analyze_with_specific_provider(symbol: str, preferred_provider: str):
    '''Analyze with specific provider preference'''
    
    # Temporarily switch to preferred provider
    original_provider = enhanced_provider_manager.get_current_provider_name()
    enhanced_provider_manager.set_preferred_provider(preferred_provider)
    
    try:
        analysis = analyze_stock_with_fallback(symbol)
        return analysis
    finally:
        # Restore original provider
        if original_provider:
            enhanced_provider_manager.set_preferred_provider(original_provider)
"""
    
    print("📝 Example integration code:")
    print(example_code)

if __name__ == "__main__":
    print("🚀 Enhanced Provider System Integration")
    print("=" * 60)
    
    # Main setup
    setup_success = setup_enhanced_provider_system()
    
    if setup_success:
        # Test provider switching
        test_provider_switching()
        
        # Show integration examples
        show_integration_example()
        
        print("\n🏆 Integration Complete!")
        print("✨ Your enhanced provider system is ready for production!")
    else:
        print("\n❌ Setup failed - check errors above")
    
    sys.exit(0 if setup_success else 1)