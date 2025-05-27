"""
Test script for Technical Analysis Agent
Creates sample data and tests the technical analysis functionality
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.agents.data_agents.technical_agent import TechnicalAnalysisAgent

def create_sample_price_data(days: int = 100, start_price: float = 100.0) -> pd.DataFrame:
    """Create sample price data for testing"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days-1), periods=days, freq='D')
    
    # Generate realistic price movements
    np.random.seed(42)  # For reproducible results
    returns = np.random.normal(0.001, 0.02, days)  # Daily returns with slight upward bias
    
    prices = [start_price]
    for i in range(1, days):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, 1.0))  # Ensure prices don't go negative
    
    # Create DataFrame with OHLCV data
    price_data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Generate realistic OHLV from close prices
        volatility = abs(np.random.normal(0, 0.015))
        high = close * (1 + volatility)
        low = close * (1 - volatility)
        open_price = low + (high - low) * np.random.random()
        volume = int(np.random.uniform(100000, 1000000))
        
        price_data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(price_data)
    df.set_index('date', inplace=True)
    return df

def test_technical_agent():
    """Test the Technical Analysis Agent"""
    print("🧪 Testing Technical Analysis Agent...")
    print("=" * 50)
    
    # Create Technical Analysis Agent
    agent = TechnicalAnalysisAgent()
    print(f"✅ Created {agent.name} agent")
    
    # Create sample data
    print("\n📊 Creating sample price data...")
    sample_data = create_sample_price_data(days=250, start_price=150.0)
    print(f"✅ Created {len(sample_data)} days of sample price data")
    print(f"   Price range: ₹{sample_data['low'].min():.2f} - ₹{sample_data['high'].max():.2f}")
    print(f"   Latest close: ₹{sample_data['close'].iloc[-1]:.2f}")
    
    # Test the agent
    print("\n🔍 Running technical analysis...")
    
    data_input = {
        'price_data': sample_data
    }
    
    # Get recommendation
    recommendation = agent.get_recommendation('TEST_STOCK', data_input)
    
    print(f"✅ Analysis completed!")
    print("\n📈 RECOMMENDATION RESULTS:")
    print("=" * 30)
    print(f"Stock: TEST_STOCK")
    print(f"Action: {recommendation['action']}")
    print(f"Confidence: {recommendation['confidence']:.2f}")
    print(f"Agent: {recommendation['agent_name']}")
    print(f"Reasoning: {recommendation['reasoning']}")
    
    # Display key technical indicators
    if 'additional_data' in recommendation:
        indicators = recommendation['additional_data'].get('indicators', {})
        
        print(f"\n📊 TECHNICAL INDICATORS:")
        print("-" * 25)
        
        # RSI
        if 'RSI' in indicators:
            rsi_data = indicators['RSI']
            print(f"RSI (14): {rsi_data['current']:.1f} - {rsi_data['signal']}")
        
        # MACD
        if 'MACD' in indicators:
            macd_data = indicators['MACD']
            print(f"MACD: {macd_data['macd']:.2f} - {macd_data['signal_interpretation']}")
        
        # Moving Averages
        if 'MovingAverages' in indicators:
            ma_data = indicators['MovingAverages']
            current_price = ma_data['current_price']
            print(f"Current Price: ₹{current_price:.2f}")
            
            for sma_name, sma_value in ma_data['sma'].items():
                print(f"{sma_name}: ₹{sma_value:.2f}")
        
        # Trend Analysis
        trend_data = recommendation['additional_data'].get('trend_analysis', {})
        if trend_data:
            print(f"\n📈 TREND ANALYSIS:")
            print("-" * 18)
            print(f"Overall Trend: {trend_data.get('overall_trend', 'N/A')}")
            print(f"Short-term (5d): {trend_data.get('short_trend_pct', 0):.1f}%")
            print(f"Medium-term (20d): {trend_data.get('medium_trend_pct', 0):.1f}%")
        
        # Support & Resistance
        sr_data = recommendation['additional_data'].get('support_resistance', {})
        if sr_data:
            print(f"\n🎯 SUPPORT & RESISTANCE:")
            print("-" * 25)
            print(f"Support: ₹{sr_data.get('support_level', 0):.2f}")
            print(f"Resistance: ₹{sr_data.get('resistance_level', 0):.2f}")
            print(f"Current: ₹{sr_data.get('current_price', 0):.2f}")
    
    print(f"\n🎉 Technical Analysis Agent test completed successfully!")
    print(f"The agent is working and generating {recommendation['action']} recommendations!")
    
    return recommendation

if __name__ == "__main__":
    try:
        test_technical_agent()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()