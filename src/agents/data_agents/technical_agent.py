"""
Technical Analysis Agent
Performs technical analysis using various indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.agents.base_agent import BaseAgent
from config.settings import AGENT_CONFIG

class TechnicalAnalysisAgent(BaseAgent):
    """Technical Analysis Agent using various technical indicators"""
    
    def __init__(self, config: Dict[str, Any] = None):
        # Use config from settings if not provided
        agent_config = config or AGENT_CONFIG.get('technical_agent', {})
        super().__init__("TechnicalAnalysis", agent_config)
        
        # Technical analysis specific settings
        self.indicators = self.config.get('indicators', ['RSI', 'MACD', 'SMA', 'EMA'])
        self.lookback_periods = self.config.get('lookback_periods', [14, 21, 50, 200])
        
        self.logger.info(f"Technical Analysis Agent initialized with indicators: {self.indicators}")
    
    def analyze(self, stock_symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform technical analysis on stock data
        
        Args:
            stock_symbol: Stock symbol
            data: Dictionary containing 'price_data' as pandas DataFrame
            
        Returns:
            Dictionary with technical analysis results
        """
        required_fields = ['price_data']
        if not self.validate_data(data, required_fields):
            return {'error': 'Missing required price data'}
        
        price_df = data['price_data']
        
        # Validate price data structure
        required_columns = ['close', 'high', 'low', 'volume']
        if not all(col in price_df.columns for col in required_columns):
            return {'error': f'Missing required columns in price data: {required_columns}'}
        
        if len(price_df) < max(self.lookback_periods):
            return {'error': f'Insufficient data. Need at least {max(self.lookback_periods)} days'}
        
        # Calculate all technical indicators
        analysis_result = {
            'stock_symbol': stock_symbol,
            'analysis_date': datetime.now(),
            'indicators': {},
            'signals': {},
            'trend_analysis': {},
            'support_resistance': {}
        }
        
        try:
            # Calculate RSI
            if 'RSI' in self.indicators:
                rsi_values = self._calculate_rsi(price_df['close'])
                analysis_result['indicators']['RSI'] = {
                    'current': rsi_values.iloc[-1],
                    'previous': rsi_values.iloc[-2] if len(rsi_values) > 1 else None,
                    'signal': self._interpret_rsi(rsi_values.iloc[-1])
                }
            
            # Calculate MACD
            if 'MACD' in self.indicators:
                macd_data = self._calculate_macd(price_df['close'])
                analysis_result['indicators']['MACD'] = {
                    'macd': macd_data['macd'].iloc[-1],
                    'signal': macd_data['signal'].iloc[-1],
                    'histogram': macd_data['histogram'].iloc[-1],
                    'signal_interpretation': self._interpret_macd(macd_data)
                }
            
            # Calculate Moving Averages
            if 'SMA' in self.indicators or 'EMA' in self.indicators:
                ma_analysis = self._calculate_moving_averages(price_df['close'])
                analysis_result['indicators']['MovingAverages'] = ma_analysis
            
            # Calculate Bollinger Bands
            if 'BB' in self.indicators:
                bb_data = self._calculate_bollinger_bands(price_df['close'])
                analysis_result['indicators']['BollingerBands'] = {
                    'upper': bb_data['upper'].iloc[-1],
                    'middle': bb_data['middle'].iloc[-1],
                    'lower': bb_data['lower'].iloc[-1],
                    'position': self._interpret_bollinger_position(price_df['close'].iloc[-1], bb_data),
                    'signal': self._interpret_bollinger_bands(price_df['close'].iloc[-1], bb_data)
                }
            
            # Calculate Volume Analysis
            volume_analysis = self._analyze_volume(price_df)
            analysis_result['indicators']['Volume'] = volume_analysis
            
            # Trend Analysis
            trend_analysis = self._analyze_trend(price_df)
            analysis_result['trend_analysis'] = trend_analysis
            
            # Support and Resistance
            support_resistance = self._calculate_support_resistance(price_df)
            analysis_result['support_resistance'] = support_resistance
            
            # Generate overall technical signals
            technical_signals = self._generate_technical_signals(analysis_result)
            analysis_result['signals'] = technical_signals
            
            self.logger.info(f"Technical analysis completed for {stock_symbol}")
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {stock_symbol}: {e}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _interpret_rsi(self, rsi_value: float) -> str:
        """Interpret RSI signal"""
        if rsi_value > 70:
            return "OVERBOUGHT"
        elif rsi_value < 30:
            return "OVERSOLD"
        elif rsi_value > 50:
            return "BULLISH"
        else:
            return "BEARISH"
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return {
            'macd': macd,
            'signal': signal,
            'histogram': histogram
        }
    
    def _interpret_macd(self, macd_data: Dict[str, pd.Series]) -> str:
        """Interpret MACD signal"""
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        current_histogram = macd_data['histogram'].iloc[-1]
        
        if current_macd > current_signal and current_histogram > 0:
            return "BULLISH"
        elif current_macd < current_signal and current_histogram < 0:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _calculate_moving_averages(self, prices: pd.Series) -> Dict[str, Any]:
        """Calculate various moving averages"""
        current_price = prices.iloc[-1]
        
        ma_analysis = {
            'current_price': current_price,
            'sma': {},
            'ema': {},
            'trend_signals': []
        }
        
        # Calculate SMAs and EMAs for different periods
        for period in [20, 50, 200]:
            if len(prices) >= period:
                sma = prices.rolling(window=period).mean().iloc[-1]
                ema = prices.ewm(span=period).mean().iloc[-1]
                
                ma_analysis['sma'][f'SMA_{period}'] = sma
                ma_analysis['ema'][f'EMA_{period}'] = ema
                
                # Generate signals based on price vs MA
                if current_price > sma:
                    ma_analysis['trend_signals'].append(f"Above SMA_{period}")
                else:
                    ma_analysis['trend_signals'].append(f"Below SMA_{period}")
        
        return ma_analysis
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    def _interpret_bollinger_position(self, current_price: float, bb_data: Dict[str, pd.Series]) -> str:
        """Determine position relative to Bollinger Bands"""
        upper = bb_data['upper'].iloc[-1]
        lower = bb_data['lower'].iloc[-1]
        
        if current_price > upper:
            return "ABOVE_UPPER"
        elif current_price < lower:
            return "BELOW_LOWER"
        else:
            return "WITHIN_BANDS"
    
    def _interpret_bollinger_bands(self, current_price: float, bb_data: Dict[str, pd.Series]) -> str:
        """Interpret Bollinger Bands signal"""
        position = self._interpret_bollinger_position(current_price, bb_data)
        
        if position == "ABOVE_UPPER":
            return "OVERBOUGHT"
        elif position == "BELOW_LOWER":
            return "OVERSOLD"
        else:
            return "NEUTRAL"
    
    def _analyze_volume(self, price_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns"""
        volume = price_df['volume']
        close = price_df['close']
        
        avg_volume_20 = volume.rolling(window=20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        
        # Price-Volume relationship
        price_change = close.pct_change().iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
        
        volume_signal = "NEUTRAL"
        if volume_ratio > 1.5:  # High volume
            if price_change > 0:
                volume_signal = "BULLISH_BREAKOUT"
            else:
                volume_signal = "BEARISH_BREAKOUT"
        elif volume_ratio < 0.5:  # Low volume
            volume_signal = "LOW_CONVICTION"
        
        return {
            'current_volume': current_volume,
            'avg_volume_20': avg_volume_20,
            'volume_ratio': volume_ratio,
            'volume_signal': volume_signal
        }
    
    def _analyze_trend(self, price_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trend"""
        close = price_df['close']
        
        # Short-term trend (5 days)
        short_trend = close.iloc[-1] / close.iloc[-6] - 1 if len(close) >= 6 else 0
        
        # Medium-term trend (20 days)
        medium_trend = close.iloc[-1] / close.iloc[-21] - 1 if len(close) >= 21 else 0
        
        # Long-term trend (50 days)
        long_trend = close.iloc[-1] / close.iloc[-51] - 1 if len(close) >= 51 else 0
        
        # Determine overall trend
        if short_trend > 0.02 and medium_trend > 0.05:
            overall_trend = "STRONG_UPTREND"
        elif short_trend > 0 and medium_trend > 0:
            overall_trend = "UPTREND"
        elif short_trend < -0.02 and medium_trend < -0.05:
            overall_trend = "STRONG_DOWNTREND"
        elif short_trend < 0 and medium_trend < 0:
            overall_trend = "DOWNTREND"
        else:
            overall_trend = "SIDEWAYS"
        
        return {
            'short_trend_pct': short_trend * 100,
            'medium_trend_pct': medium_trend * 100,
            'long_trend_pct': long_trend * 100,
            'overall_trend': overall_trend
        }
    
    def _calculate_support_resistance(self, price_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic support and resistance levels"""
        high = price_df['high']
        low = price_df['low']
        close = price_df['close']
        
        # Simple support/resistance based on recent highs and lows
        recent_high = high.rolling(window=20).max().iloc[-1]
        recent_low = low.rolling(window=20).min().iloc[-1]
        current_price = close.iloc[-1]
        
        # Distance from support/resistance
        resistance_distance = (recent_high - current_price) / current_price
        support_distance = (current_price - recent_low) / current_price
        
        return {
            'resistance_level': recent_high,
            'support_level': recent_low,
            'current_price': current_price,
            'resistance_distance_pct': resistance_distance * 100,
            'support_distance_pct': support_distance * 100
        }
    
    def _generate_technical_signals(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall technical signals from all indicators"""
        signals = []
        
        # RSI signals
        if 'RSI' in analysis_result['indicators']:
            rsi_signal = analysis_result['indicators']['RSI']['signal']
            if rsi_signal == "OVERSOLD":
                signals.append(0.7)  # Bullish
            elif rsi_signal == "OVERBOUGHT":
                signals.append(-0.7)  # Bearish
            elif rsi_signal == "BULLISH":
                signals.append(0.3)
            elif rsi_signal == "BEARISH":
                signals.append(-0.3)
        
        # MACD signals
        if 'MACD' in analysis_result['indicators']:
            macd_signal = analysis_result['indicators']['MACD']['signal_interpretation']
            if macd_signal == "BULLISH":
                signals.append(0.6)
            elif macd_signal == "BEARISH":
                signals.append(-0.6)
        
        # Trend signals
        if 'trend_analysis' in analysis_result:
            trend = analysis_result['trend_analysis']['overall_trend']
            if trend == "STRONG_UPTREND":
                signals.append(0.8)
            elif trend == "UPTREND":
                signals.append(0.4)
            elif trend == "STRONG_DOWNTREND":
                signals.append(-0.8)
            elif trend == "DOWNTREND":
                signals.append(-0.4)
        
        # Calculate overall signal
        if signals:
            overall_signal = sum(signals) / len(signals)
        else:
            overall_signal = 0
        
        return {
            'individual_signals': signals,
            'overall_signal': overall_signal,
            'signal_strength': abs(overall_signal),
            'signal_direction': "BULLISH" if overall_signal > 0 else "BEARISH" if overall_signal < 0 else "NEUTRAL"
        }
    
    def _generate_recommendation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading recommendation from technical analysis"""
        if 'error' in analysis_result:
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': f"Technical analysis error: {analysis_result['error']}"
            }
        
        signals = analysis_result.get('signals', {})
        overall_signal = signals.get('overall_signal', 0)
        signal_strength = signals.get('signal_strength', 0)
        
        # Determine action based on signal strength and direction
        if signal_strength >= self.confidence_threshold:
            if overall_signal > 0:
                action = "BUY"
            else:
                action = "SELL"
        else:
            action = "HOLD"
        
        # Generate reasoning
        reasoning_parts = []
        
        # Add key technical insights
        if 'RSI' in analysis_result['indicators']:
            rsi_signal = analysis_result['indicators']['RSI']['signal']
            reasoning_parts.append(f"RSI: {rsi_signal}")
        
        if 'MACD' in analysis_result['indicators']:
            macd_signal = analysis_result['indicators']['MACD']['signal_interpretation']
            reasoning_parts.append(f"MACD: {macd_signal}")
        
        if 'trend_analysis' in analysis_result:
            trend = analysis_result['trend_analysis']['overall_trend']
            reasoning_parts.append(f"Trend: {trend}")
        
        reasoning = f"Technical Analysis - {', '.join(reasoning_parts)}"
        
        return {
            'action': action,
            'confidence': signal_strength,
            'reasoning': reasoning,
            'technical_score': overall_signal,
            'additional_data': {
                'indicators': analysis_result.get('indicators', {}),
                'trend_analysis': analysis_result.get('trend_analysis', {}),
                'support_resistance': analysis_result.get('support_resistance', {})
            }
        }