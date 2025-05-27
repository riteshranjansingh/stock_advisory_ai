"""
Test Credentials Script
Check and validate broker API credentials
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.credentials import credentials_manager

def test_credentials():
    """Test credential loading and validation"""
    print("🔐 AI Trading System - Credentials Test")
    print("=" * 40)
    
    # Get credentials status
    status = credentials_manager.get_status()
    
    print(f"📊 CREDENTIALS STATUS:")
    print("-" * 25)
    print(f"Total Configured Brokers: {status['total_brokers_configured']}")
    print(f"Available Brokers: {len(status['available_brokers'])}")
    print(f"Missing Brokers: {len(status['missing_brokers'])}")
    print()
    
    # Show available brokers
    if status['available_brokers']:
        print("✅ CONFIGURED BROKERS:")
        print("-" * 22)
        for broker in status['available_brokers']:
            valid_icon = "✅" if broker['valid'] else "❌"
            print(f"  {valid_icon} {broker['name'].upper()}")
            
            # Show masked credentials
            for key, value in broker['credentials'].items():
                if key != 'broker_name':
                    print(f"     {key}: {value}")
        print()
    
    # Show missing brokers
    if status['missing_brokers']:
        print("❌ MISSING BROKERS:")
        print("-" * 18)
        for broker in status['missing_brokers']:
            print(f"  • {broker.upper()}")
        print()
        
        print("📝 TO ADD CREDENTIALS:")
        print("-" * 22)
        print("1. Edit your .env file")
        print("2. Add the required environment variables")
        print("3. Restart your application")
        print()
        
        print("🔗 WHERE TO GET API CREDENTIALS:")
        print("-" * 32)
        print("• Fyers: https://myapi.fyers.in/")
        print("• Shoonya: https://shoonya.finvasia.com/")
        print("• MStock: https://www.miraeassetcm.com/")
        print("• Upstox: https://developer.upstox.com/")
        print("• Dhan: https://dhanhq.co/")
        print("• Kite: https://kite.trade/")
        print()
    
    # Show next steps
    if status['total_brokers_configured'] == 0:
        print("🚀 NEXT STEPS:")
        print("-" * 13)
        print("1. Choose your primary broker (Fyers recommended)")
        print("2. Get API credentials from broker's developer portal")
        print("3. Add credentials to .env file")
        print("4. Run this test again to verify")
        print()
        print("💡 TIP: Start with just one broker, add others later!")
    else:
        print("🎉 GREAT! You have broker credentials configured!")
        print("Run the main provider test to see them in action.")

def show_env_template():
    """Show .env file template"""
    print("\n📄 .ENV FILE TEMPLATE:")
    print("-" * 22)
    print("Copy this template to your .env file and fill in your credentials:")
    print()
    print("""# Fyers (Recommended as primary)
FYERS_CLIENT_ID=your_fyers_client_id
FYERS_ACCESS_TOKEN=your_fyers_access_token

# Shoonya (Good fallback)
SHOONYA_USER_ID=your_user_id
SHOONYA_PASSWORD=your_password
SHOONYA_API_KEY=your_api_key

# Add other brokers as needed...
""")

def main():
    """Main function"""
    test_credentials()
    
    # Show template if no credentials found
    status = credentials_manager.get_status()
    if status['total_brokers_configured'] == 0:
        show_env_template()

if __name__ == "__main__":
    main()