"""
Sample Data Provider
Provides realistic sample data when real APIs are unavailable
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from .base_provider import BaseDataProvider, DataProviderPriority, DataProviderStatus

class SampleDataProvider(BaseDataProvider):
    """Sample data provider for testing and fallback"""
    
    def __init__(self):
        super().__init__("SampleData", DataProviderPriority.BACKUP)
        
        # Sample stock database
        self.stock_database = {
            'RELIANCE': {
                'name': 'Reliance Industries Limited',
                'sector': 'Oil & Gas',
                'industry': 'Petroleum Products',
                'market_cap': 1500000,
                'base_price': 2800,
                'volatility': 0.018
            },
            'TCS': {
                'name': 'Tata Consultancy Services',
                'sector': 'IT Services',
                'industry': 'Software Services',
                'market_cap': 1200000,
                'base_price': 3500,
                'volatility': 0.015
            },
            'INFY': {
                'name': 'Infosys Limited',
                'sector': 'IT Services',
                'industry': 'Software Services',
                'market_cap': 800000,
                'base_price': 1800,
                'volatility': 0.016
            },
            'HDFCBANK': {
                'name': 'HDFC Bank Limited',
                'sector': 'Banking',
                'industry': 'Private Sector Bank',
                'market_cap': 900000,
                'base_price': 1600,
                'volatility': 0.020
            },
            'ICICIBANK': {
                'name': 'ICICI Bank Limited',
                'sector': 'Banking',
                'industry': 'Private Sector Bank',
                'market_cap': 600000,
                'base_price': 1200,
                'volatility': 0.022
            },
            'ITC': {
                'name': 'ITC Limited',
                'sector': 'FMCG',
                'industry': 'Tobacco & Cigarettes',
                'market_cap': 550000,
                'base_price': 450,
                'volatility': 0.014
            },
            'HINDUNILVR': {
                'name': 'Hindustan Unilever Limited',
                'sector': 'FMCG',
                'industry': 'Personal Care',
                'market_cap': 520000,
                'base_price': 2200,
                'volatility': 0.013
            },
            'SBIN': {
                'name': 'State Bank of India',
                'sector': 'Banking',
                'industry': 'Public Sector Bank',
                'market_cap': 450000,
                'base_price': 750,
                'volatility': 0.025
            },
            'BHARTIARTL': {
                'name': 'Bharti Airtel Limited',
                'sector': 'Telecom',
                'industry': 'Telecom Services',
                'market_cap': 400000,
                'base_price': 1100,
                'volatility': 0.019
            },
            'KOTAKBANK': {
                'name': 'Kotak Mahindra Bank Limited',
                'sector': 'Banking',
                'industry': 'Private Sector Bank',
                'market_cap': 380000,
                'base_price': 1900,
                'volatility': 0.021
            }
        }
        
        # Set to active immediately since it doesn't require authentication
        self.status = DataProviderStatus.ACTIVE
        self.logger.info("Sample data provider initialized with realistic data")
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Sample provider doesn't need authentication"""
        self.status = DataProviderStatus.ACTIVE
        return True
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock information from sample database"""
        symbol = symbol.upper()
        
        if symbol not in self.stock_database:
            self.logger.debug(f"Stock {symbol} not in sample database")
            # Don't return None, raise DataNotFoundError instead
            from .base_provider import DataNotFoundError
            raise DataNotFoundError(self.name, symbol, f"Stock {symbol} not found in sample database")
        
        stock_data = self.stock_database[symbol]
        
        return {
            'symbol': symbol,
            'name': stock_data['name'],
            'sector': stock_data['sector'],
            'industry': stock_data['industry'],
            'market_cap': stock_data['market_cap'],
            'exchange': 'NSE'
        }
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """Generate realistic historical data"""
        symbol = symbol.upper()
        
        if symbol not in self.stock_database:
            return None
        
        stock_info = self.stock_database[symbol]
        base_price = stock_info['base_price']
        volatility = stock_info['volatility']
        
        # Calculate number of days
        days = (end_date - start_date).days + 1
        
        if days <= 0:
            return None
        
        # Generate dates
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Filter out weekends (crude market hours simulation)
        business_dates = [d for d in dates if d.weekday() < 5]
        
        if not business_dates:
            return None
        
        # Generate realistic price movements
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
        
        # Create a trend component (slight upward bias for most stocks)
        trend_factor = 0.0002 if stock_info['sector'] in ['IT Services', 'Banking'] else 0.0001
        
        daily_returns = np.random.normal(trend_factor, volatility, len(business_dates))
        
        # Generate prices
        prices = [base_price]
        for i in range(1, len(business_dates)):
            new_price = prices[-1] * (1 + daily_returns[i])
            prices.append(max(new_price, base_price * 0.5))  # Floor at 50% of base
        
        # Create OHLCV data
        historical_data = []
        for i, (date, close) in enumerate(zip(business_dates, prices)):
            # Generate realistic intraday movements
            daily_vol = abs(np.random.normal(0, volatility * 0.7))
            high = close * (1 + daily_vol)
            low = close * (1 - daily_vol)
            
            # Open price influenced by previous close
            if i == 0:
                open_price = close * (1 + np.random.normal(0, 0.005))
            else:
                gap = np.random.normal(0, 0.003)  # Small gaps
                open_price = prices[i-1] * (1 + gap)
            
            # Ensure OHLC consistency
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            # Generate realistic volume
            base_volume = 1000000 if stock_info['market_cap'] > 1000000 else 500000
            volume_multiplier = abs(np.random.normal(1.0, 0.5))
            volume = int(base_volume * volume_multiplier)
            
            historical_data.append({
                'date': date.date(),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
        
        df = pd.DataFrame(historical_data)
        self.logger.info(f"Generated {len(df)} days of sample data for {symbol}")
        
        return df
    
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Generate realistic real-time data"""
        result = {}
        
        for symbol in symbols:
            symbol = symbol.upper()
            
            if symbol not in self.stock_database:
                continue
            
            stock_info = self.stock_database[symbol]
            base_price = stock_info['base_price']
            volatility = stock_info['volatility']
            
            # Generate current price with some random movement
            current_price = base_price * (1 + np.random.normal(0, volatility))
            prev_close = base_price * (1 + np.random.normal(0, volatility * 0.5))
            
            # Generate intraday high/low
            daily_range = volatility * 0.8
            high = current_price * (1 + abs(np.random.normal(0, daily_range)))
            low = current_price * (1 - abs(np.random.normal(0, daily_range)))
            open_price = low + (high - low) * np.random.random()
            
            # Calculate change
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            
            # Generate volume
            base_volume = 1000000 if stock_info['market_cap'] > 1000000 else 500000
            volume = int(base_volume * abs(np.random.normal(1.0, 0.3)))
            
            result[symbol] = {
                'symbol': symbol,
                'ltp': round(current_price, 2),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(prev_close, 2),
                'volume': volume,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'timestamp': datetime.now()
            }
        
        return result
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search stocks in sample database"""
        query = query.upper()
        results = []
        
        for symbol, info in self.stock_database.items():
            if (query in symbol or 
                query in info['name'].upper() or 
                query in info['sector'].upper()):
                
                results.append({
                    'symbol': symbol,
                    'name': info['name'],
                    'sector': info['sector'],
                    'market_cap': info['market_cap']
                })
        
        return results
    
    def add_sample_stock(self, symbol: str, name: str, sector: str, 
                        base_price: float, market_cap: float, volatility: float = 0.02):
        """Add a new stock to sample database"""
        self.stock_database[symbol.upper()] = {
            'name': name,
            'sector': sector,
            'industry': sector,  # Simplified
            'market_cap': market_cap,
            'base_price': base_price,
            'volatility': volatility
        }
        
        self.logger.info(f"Added sample stock: {symbol}")
    
    def get_available_symbols(self) -> List[str]:
        """Get all available symbols in sample database"""
        return list(self.stock_database.keys())