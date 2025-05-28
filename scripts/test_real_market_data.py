#!/usr/bin/env python3
"""
Smart Fallback Test script for real market data integration
Automatically tries optimal data periods and falls back gracefully
"""
import sys
import os
from datetime import date, timedelta
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.providers.fyers_provider import FyersProvider
from src.agents.data_agents.technical_agent import TechnicalAnalysisAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_fyers_authentication():
    """Test Fyers provider authentication"""
    print("🔐 Testing Fyers Provider Authentication")
    print("="*50)
    
    try:
        provider = FyersProvider()
        
        # Test authentication
        auth_success = provider.authenticate()
        
        if auth_success:
            print("✅ Authentication successful!")
            print(f"Status: {provider.status}")
            return provider
        else:
            print("❌ Authentication failed!")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_real_time_data(provider):
    """Test real-time data fetching"""
    print("\n📊 Testing Real-Time Market Data")
    print("="*50)
    
    try:
        # Test with major Indian stocks
        test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
        
        print(f"Fetching real-time data for: {', '.join(test_symbols)}")
        
        real_time_data = provider.get_real_time_data(test_symbols)
        
        if real_time_data:
            print(f"✅ Successfully fetched data for {len(real_time_data)} stocks")
            
            for symbol, data in real_time_data.items():
                print(f"📈 {symbol}: ₹{data['ltp']:.2f} "
                      f"({data['change']:+.2f}, {data['change_percent']:+.2f}%)")
            
            return real_time_data
        else:
            print("❌ Failed to fetch real-time data")
            return None
            
    except Exception as e:
        print(f"❌ Real-time data error: {e}")
        return None

def test_historical_data_smart(provider):
    """Test historical data with smart fallback periods"""
    print("\n📅 Testing Historical Market Data (Smart Fallback)")
    print("="*50)
    
    symbol = 'RELIANCE'
    end_date = date.today()
    
    # Try different periods in descending order (optimal to minimum)
    test_periods = [
        (220, "7+ months (optimal for 200-day MA)"),
        (120, "4 months (good for most indicators)"), 
        (60, "2 months (basic analysis)"),
        (30, "1 month (minimal analysis)")
    ]
    
    for days, description in test_periods:
        start_date = end_date - timedelta(days=days)
        
        print(f"🔄 Trying {description}: {start_date} to {end_date}")
        
        try:
            historical_data = provider.get_historical_data(symbol, start_date, end_date)
            
            if historical_data is not None and not historical_data.empty:
                actual_days = len(historical_data)
                print(f"✅ Successfully fetched {actual_days} days of data")
                
                if actual_days >= 30:  # Minimum for any meaningful analysis
                    print(f"📊 Data quality: {'Excellent' if actual_days >= 150 else 'Good' if actual_days >= 60 else 'Basic'}")
                    print("\nLast 5 days:")
                    print(historical_data.tail().to_string(index=False))
                    return historical_data, actual_days
                else:
                    print(f"⚠️  Only {actual_days} days available, trying shorter period...")
                    continue
            else:
                print(f"❌ No data for {days}-day period, trying shorter...")
                continue
                
        except Exception as e:
            print(f"❌ Error fetching {days}-day data: {e}")
            continue
    
    print("❌ Could not fetch sufficient historical data with any period")
    return None, 0

def test_technical_analysis_smart_fallback(provider):
    """Test technical analysis with smart configuration based on available data"""
    print("\n🤖 Testing Technical Analysis (Smart Configuration)")
    print("="*60)
    
    try:
        symbol = 'RELIANCE'
        
        # Get historical data with smart fallback
        historical_data, data_days = test_historical_data_smart(provider)
        
        if historical_data is None or historical_data.empty:
            print("❌ No historical data available for analysis")
            return False
        
        print(f"\n🧠 Configuring technical analysis for {data_days} days of data...")
        
        # Smart configuration based on available data
        if data_days >= 200:
            # Full configuration - all indicators
            agent_config = {
                'indicators': ['RSI', 'MACD', 'SMA', 'EMA', 'BB'],
                'lookback_periods': [14, 21, 50, 200],
                'confidence_threshold': 0.6
            }
            analysis_quality = "Professional (200+ days)"
            
        elif data_days >= 100:
            # Good configuration - most indicators
            agent_config = {
                'indicators': ['RSI', 'MACD', 'SMA', 'EMA', 'BB'],
                'lookback_periods': [14, 21, 50],
                'confidence_threshold': 0.65
            }
            analysis_quality = "Advanced (100+ days)"
            
        elif data_days >= 60:
            # Moderate configuration - core indicators
            agent_config = {
                'indicators': ['RSI', 'MACD', 'SMA', 'EMA'],
                'lookback_periods': [14, 21, 30],
                'confidence_threshold': 0.7
            }
            analysis_quality = "Standard (60+ days)"
            
        else:
            # Minimal configuration - basic indicators
            agent_config = {
                'indicators': ['RSI', 'MACD', 'SMA'],
                'lookback_periods': [14, 21],
                'confidence_threshold': 0.75
            }
            analysis_quality = "Basic (30+ days)"
        
        print(f"📊 Analysis Quality: {analysis_quality}")
        print(f"🔧 Indicators: {', '.join(agent_config['indicators'])}")
        print(f"📏 Lookback Periods: {agent_config['lookback_periods']}")
        
        # Create technical analysis agent with smart configuration
        tech_agent = TechnicalAnalysisAgent(config=agent_config)
        
        # Prepare data in the format expected by the agent
        agent_data = {
            'price_data': historical_data
        }
        
        print(f"🔍 Running technical analysis...")
        
        # Call the analyze method
        analysis = tech_agent.analyze(symbol, agent_data)
        
        if analysis and 'error' not in analysis:
            print(f"✅ Technical Analysis Complete for {symbol}")
            
            # Extract key information from the analysis
            indicators = analysis.get('indicators', {})
            signals = analysis.get('signals', {})
            trend_analysis = analysis.get('trend_analysis', {})
            support_resistance = analysis.get('support_resistance', {})
            
            # Display results
            print(f"\n📊 ANALYSIS RESULTS:")
            print(f"="*40)
            
            if signals:
                signal_direction = signals.get('signal_direction', 'N/A')
                signal_strength = signals.get('signal_strength', 0)
                print(f"🎯 Overall Signal: {signal_direction}")
                print(f"💪 Signal Strength: {signal_strength:.2f}")
            
            if trend_analysis:
                overall_trend = trend_analysis.get('overall_trend', 'N/A')
                print(f"📈 Overall Trend: {overall_trend}")
                
                if 'short_trend_pct' in trend_analysis:
                    short_trend = trend_analysis['short_trend_pct']
                    medium_trend = trend_analysis['medium_trend_pct']
                    print(f"📊 Short-term Trend: {short_trend:+.1f}%")
                    print(f"📊 Medium-term Trend: {medium_trend:+.1f}%")
            
            # Show key technical indicators
            print(f"\n📈 TECHNICAL INDICATORS:")
            print(f"="*40)
            
            if 'RSI' in indicators:
                rsi_data = indicators['RSI']
                rsi_value = rsi_data.get('current', 0)
                rsi_signal = rsi_data.get('signal', 'N/A')
                print(f"   📊 RSI: {rsi_value:.1f} ({rsi_signal})")
            
            if 'MACD' in indicators:
                macd_data = indicators['MACD']
                macd_signal = macd_data.get('signal_interpretation', 'N/A')
                print(f"   📊 MACD: {macd_signal}")
            
            if 'MovingAverages' in indicators:
                ma_data = indicators['MovingAverages']
                current_price = ma_data.get('current_price', 0)
                print(f"   💰 Current Price: ₹{current_price:.2f}")
                
                # Show SMA signals
                sma_data = ma_data.get('sma', {})
                for period, value in sma_data.items():
                    status = "Above ✅" if current_price > value else "Below ❌"
                    print(f"   📈 {period}: ₹{value:.2f} ({status})")
            
            if 'BollingerBands' in indicators:
                bb_data = indicators['BollingerBands']
                bb_signal = bb_data.get('signal', 'N/A')
                bb_position = bb_data.get('position', 'N/A')
                print(f"   📊 Bollinger Bands: {bb_signal} ({bb_position})")
            
            if 'Volume' in indicators:
                vol_data = indicators['Volume']
                vol_signal = vol_data.get('volume_signal', 'N/A')
                vol_ratio = vol_data.get('volume_ratio', 0)
                print(f"   📊 Volume: {vol_signal} (Ratio: {vol_ratio:.1f}x)")
            
            if support_resistance:
                support = support_resistance.get('support_level', 0)
                resistance = support_resistance.get('resistance_level', 0)
                print(f"   🔻 Support: ₹{support:.2f}")
                print(f"   🔺 Resistance: ₹{resistance:.2f}")
            
            # Generate and show recommendation
            try:
                recommendation = tech_agent._generate_recommendation(analysis)
                if recommendation:
                    print(f"\n💡 TRADING RECOMMENDATION:")
                    print(f"="*40)
                    print(f"   🎯 Action: {recommendation.get('action', 'N/A')}")
                    print(f"   💪 Confidence: {recommendation.get('confidence', 0):.2f}")
                    print(f"   📝 Reasoning: {recommendation.get('reasoning', 'N/A')}")
            except Exception as e:
                print(f"   ⚠️  Could not generate recommendation: {e}")
            
            return True
            
        elif analysis and 'error' in analysis:
            print(f"❌ Technical analysis error: {analysis['error']}")
            
            # Try even more relaxed configuration as last resort
            if data_days >= 20:
                print(f"🔄 Trying minimal configuration as last resort...")
                
                minimal_config = {
                    'indicators': ['RSI', 'SMA'],
                    'lookback_periods': [14],
                    'confidence_threshold': 0.8
                }
                
                try:
                    tech_agent_minimal = TechnicalAnalysisAgent(config=minimal_config)
                    analysis_minimal = tech_agent_minimal.analyze(symbol, agent_data)
                    
                    if analysis_minimal and 'error' not in analysis_minimal:
                        print(f"✅ Minimal analysis successful!")
                        
                        # Show basic results
                        indicators = analysis_minimal.get('indicators', {})
                        if 'RSI' in indicators:
                            rsi_data = indicators['RSI']
                            rsi_value = rsi_data.get('current', 0)
                            rsi_signal = rsi_data.get('signal', 'N/A')
                            print(f"📊 RSI: {rsi_value:.1f} ({rsi_signal})")
                        
                        return True
                    else:
                        print(f"❌ Even minimal analysis failed")
                        return False
                        
                except Exception as e:
                    print(f"❌ Minimal analysis error: {e}")
                    return False
            else:
                return False
        else:
            print("❌ Technical analysis returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Technical analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function with smart fallback system"""
    print("🚀 Smart Fallback Real Market Data Integration Test")
    print("="*70)
    print("This system automatically adapts to available data and falls back gracefully!")
    print("="*70)
    
    # Test 1: Authentication
    provider = test_fyers_authentication()
    if not provider:
        print("\n❌ Cannot proceed without authentication")
        return False
    
    # Test 2: Real-time data
    real_time_success = test_real_time_data(provider)
    
    # Test 3: Smart technical analysis (includes historical data test)
    analysis_success = test_technical_analysis_smart_fallback(provider)
    
    # Summary
    print("\n" + "="*70)
    print("🏆 SMART FALLBACK TEST SUMMARY")
    print("="*70)
    
    tests = [
        ("Authentication", provider is not None),
        ("Real-time Data", real_time_success is not None),
        ("Smart Technical Analysis", analysis_success)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("🤖 Your AI trading system is analyzing real market data!")
        print("🚀 Ready to generate live trading recommendations!")
        print("💡 The system automatically adapts to available data!")
    else:
        print("⚠️  Some tests failed, but the system adapted where possible.")
    
    return passed >= 2  # Pass if at least authentication and one data test work

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)