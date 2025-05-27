"""
Database Initialization Script
Sets up the SQLite database with all required tables
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.database import db_manager
from config.settings import DATABASE_CONFIG
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Initialize the database"""
    print("🚀 Initializing AI Trading System Database...")
    print(f"📍 Database location: {DATABASE_CONFIG['sqlite_db_path']}")
    
    # Initialize database
    success = db_manager.initialize_database()
    
    if success:
        print("✅ Database initialized successfully!")
        
        # Add some test stocks to verify everything works
        print("\n📊 Adding sample stocks for testing...")
        
        sample_stocks = [
            ("RELIANCE", "Reliance Industries Limited", "Oil & Gas", 1500000),
            ("TCS", "Tata Consultancy Services", "IT Services", 1200000),
            ("INFY", "Infosys Limited", "IT Services", 800000),
            ("HDFCBANK", "HDFC Bank Limited", "Banking", 900000),
            ("ICICIBANK", "ICICI Bank Limited", "Banking", 600000)
        ]
        
        for symbol, name, sector, market_cap in sample_stocks:
            if db_manager.add_stock(symbol, name, sector, market_cap):
                print(f"   ✅ Added {symbol}")
            else:
                print(f"   ❌ Failed to add {symbol}")
        
        # Perform health check
        print("\n🏥 Performing database health check...")
        health = db_manager.health_check()
        
        if health['status'] == 'healthy':
            print("✅ Database health check passed!")
            print(f"   📈 Total stocks: {health['stock_count']}")
            print(f"   💾 Database path: {health['database_path']}")
        else:
            print(f"❌ Database health check failed: {health.get('error', 'Unknown error')}")
        
        print("\n🎉 Database setup complete!")
        print("Next step: Set up data ingestion pipeline")
        
    else:
        print("❌ Database initialization failed!")
        print("Check the logs for error details")
        return False
    
    return True

if __name__ == "__main__":
    main()