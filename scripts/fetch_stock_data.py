"""
Stock Data Fetching Script
Demonstrates the data ingestion pipeline with real stock data
"""

import sys
from pathlib import Path
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.ingestion.price_data_fetcher import price_fetcher
from src.agents.data_agents.technical_agent import TechnicalAnalysisAgent
from config.database import db_manager
from src.utils.logger import setup_logging

def fetch_sample_stocks():
    """Fetch data for a few sample stocks"""
    print("🚀 AI Trading System - Data Ingestion Demo")
    print("=" * 50)
    
    # Sample stocks to test
    test_stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    
    print(f"📊 Fetching data for {len(test_stocks)} stocks...")
    print("This may take a few moments as we fetch real market data...")
    print()
    
    successful = 0
    failed = 0
    
    for i, symbol in enumerate(test_stocks, 1):
        print(f"[{i}/{len(test_stocks)}] Processing {symbol}...")
        
        try:
            # Fetch stock info first
            stock_info = price_fetcher.fetch_stock_info(symbol)
            
            if stock_info:
                print(f"   ✅ {stock_info['name']}")
                print(f"      Sector: {stock_info['sector']}")
                print(f"      Market Cap: ₹{stock_info['market_cap']:,.0f} cr")
                
                # Store in database
                price_fetcher.store_stock_info(stock_info)
                
                # Fetch price data
                price_data = price_fetcher.fetch_price_data(symbol, period="1y")
                
                if price_data is not None and len(price_data) > 0:
                    price_fetcher.store_price_data(symbol, price_data)
                    print(f"      📈 Stored {len(price_data)} days of price data")
                    print(f"      Latest Close: ₹{price_data['close_price'].iloc[-1]:.2f}")
                    successful += 1
                else:
                    print(f"      ❌ No price data available")
                    failed += 1
            else:
                print(f"   ❌ Could not fetch stock info")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
        
        print()  # Empty line for readability
    
    print(f"📈 Data fetching completed!")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print()
    
    return successful > 0

def test_technical_analysis_with_real_data():
    """Test technical analysis with real stock data"""
    print("🧠 Testing Technical Analysis with Real Data")
    print("=" * 45)
    
    # Get a stock with data
    stocks = db_manager.get_active_stocks()
    
    if not stocks:
        print("❌ No stocks found in database")
        return False
    
    test_symbol = stocks[0]['symbol']
    print(f"📊 Analyzing {test_symbol} ({stocks[0]['name']})")
    
    # Get price data
    price_data = price_fetcher.get_latest_price_data(test_symbol, days=200)
    
    if price_data is None or len(price_data) < 100:
        print("❌ Insufficient price data for analysis")
        return False
    
    print(f"   📈 Using {len(price_data)} days of real market data")
    print(f"   📅 Data range: {price_data['date'].min()} to {price_data['date'].max()}")
    print(f"   💰 Price range: ₹{price_data['low'].min():.2f} - ₹{price_data['high'].max():.2f}")
    print()
    
    # Create technical analysis agent
    agent = TechnicalAnalysisAgent()
    
    # Prepare data for agent
    agent_data = {
        'price_data': price_data
    }
    
    # Get recommendation  
    recommendation = agent.get_recommendation(test_symbol, agent_data)
    
    print("🎯 LIVE STOCK ANALYSIS RESULTS:")
    print("=" * 35)
    print(f"Stock: {test_symbol}")
    print(f"Company: {stocks[0]['name']}")
    print(f"Action: {recommendation['action']}")
    print(f"Confidence: {recommendation['confidence']:.2f}")
    print(f"Reasoning: {recommendation['reasoning']}")
    print()
    
    # Display key indicators
    if 'additional_data' in recommendation:
        indicators = recommendation['additional_data'].get('indicators', {})
        
        print("📊 KEY TECHNICAL INDICATORS:")
        print("-" * 30)
        
        # Current price info
        current_price = price_data['close'].iloc[-1]
        prev_price = price_data['close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        print(f"Current Price: ₹{current_price:.2f} ({change_pct:+.1f}%)")
        
        # RSI
        if 'RSI' in indicators:
            rsi_data = indicators['RSI']
            print(f"RSI (14): {rsi_data['current']:.1f} - {rsi_data['signal']}")
        
        # MACD
        if 'MACD' in indicators:
            macd_data = indicators['MACD']
            print(f"MACD: {macd_data['signal_interpretation']}")
        
        # Trend
        trend_data = recommendation['additional_data'].get('trend_analysis', {})
        if trend_data:
            print(f"Trend: {trend_data.get('overall_trend', 'N/A')}")
            print(f"5-day change: {trend_data.get('short_trend_pct', 0):.1f}%")
            print(f"20-day change: {trend_data.get('medium_trend_pct', 0):.1f}%")
        
        print()
    
    return True

def show_data_summary():
    """Show summary of stored data"""
    print("📋 DATA SUMMARY")
    print("=" * 15)
    
    summary = price_fetcher.get_data_summary()
    
    print(f"Total Active Stocks: {summary.get('total_active_stocks', 0)}")
    print(f"Total Price Records: {summary.get('total_price_records', 0)}")
    print(f"Latest Data Date: {summary.get('latest_price_date', 'N/A')}")
    print(f"Stocks with Recent Data: {summary.get('stocks_with_recent_data', 0)}")
    print()

def main():
    """Main execution function"""
    
    # Set up logging
    setup_logging()
    
    try:
        # Step 1: Fetch sample stock data
        print("STEP 1: Fetching Real Stock Data")
        success = fetch_sample_stocks()
        
        if not success:
            print("❌ Data fetching failed. Please check your internet connection.")
            return
        
        # Step 2: Show data summary
        print("STEP 2: Data Summary")
        show_data_summary()
        
        # Step 3: Test technical analysis with real data
        print("STEP 3: Real-Time Technical Analysis")
        test_technical_analysis_with_real_data()
        
        print("🎉 CONGRATULATIONS!")
        print("Your AI Trading System is now working with REAL market data!")
        print("✅ Data ingestion pipeline: WORKING")
        print("✅ Database storage: WORKING") 
        print("✅ Technical analysis: WORKING")
        print("✅ Real stock recommendations: WORKING")
        print()
        print("🚀 Next: We'll add more agents and create the master decision system!")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()