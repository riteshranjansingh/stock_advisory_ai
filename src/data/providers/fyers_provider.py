"""
Fyers Data Provider
Implementation for Fyers broker API
"""

import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import time
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from .base_provider import (
    BaseDataProvider, DataProviderPriority, DataProviderStatus,
    DataProviderError, RateLimitError, AuthenticationError, DataNotFoundError
)

class FyersProvider(BaseDataProvider):
    """Fyers broker data provider"""
    
    def __init__(self):
        super().__init__("Fyers", DataProviderPriority.PRIMARY)
        
        # Fyers API settings
        self.base_url = "https://api-t1.fyers.in"
        self.api_version = "v3"
        self.access_token = None
        self.client_id = None
        
        # Rate limiting settings for Fyers
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.daily_request_limit = 2000  # Fyers limit
        
        # Indian market symbols format for Fyers
        self.exchange_mapping = {
            'NSE': 'NSE',
            'BSE': 'BSE'
        }
        
        self.logger.info("Fyers provider initialized")
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with Fyers API
        
        Args:
            credentials: Dict containing 'client_id' and 'access_token'
        """
        try:
            required_keys = ['client_id', 'access_token']
            for key in required_keys:
                if key not in credentials:
                    raise AuthenticationError(self.name, f"Missing required credential: {key}")
            
            self.client_id = credentials['client_id']
            self.access_token = credentials['access_token']
            
            # Test authentication with profile API
            response = self._make_request('GET', '/api/v3/profile')
            
            if response and response.get('code') == 200:
                self.status = DataProviderStatus.ACTIVE
                self.logger.info("Fyers authentication successful")
                return True
            else:
                error_msg = response.get('message', 'Authentication failed') if response else 'No response'
                raise AuthenticationError(self.name, error_msg)
                
        except Exception as e:
            self.logger.error(f"Fyers authentication failed: {e}")
            self.status = DataProviderStatus.ERROR
            return False
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to Fyers API"""
        if not self.check_rate_limit():
            raise RateLimitError(self.name)
        
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Authorization': f"{self.client_id}:{self.access_token}",
                'Content-Type': 'application/json'
            }
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            
            self.record_request()
            
            if response.status_code == 429:
                raise RateLimitError(self.name)
            
            if response.status_code == 401:
                raise AuthenticationError(self.name, "Invalid or expired token")
            
            if response.status_code != 200:
                self.logger.warning(f"HTTP {response.status_code}: {response.text}")
                return None
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise DataProviderError(self.name, str(e))
    
    def normalize_symbol(self, symbol: str, exchange: str = 'NSE') -> str:
        """Convert symbol to Fyers format"""
        # Fyers format: NSE:RELIANCE-EQ
        return f"{exchange}:{symbol}-EQ"
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock information from Fyers"""
        try:
            fyers_symbol = self.normalize_symbol(symbol)
            
            # Get symbol master data
            response = self._make_request('GET', '/api/v3/data/symbol-master', 
                                        params={'symbol': fyers_symbol})
            
            if not response or response.get('code') != 200:
                return None
            
            data = response.get('data', {})
            if not data:
                return None
            
            # Get additional market data
            quote_response = self._make_request('GET', '/api/v3/data/quotes', 
                                              params={'symbols': fyers_symbol})
            
            quote_data = {}
            if quote_response and quote_response.get('code') == 200:
                quotes = quote_response.get('d', [])
                if quotes:
                    quote_data = quotes[0]
            
            # Calculate market cap (approximate)
            market_cap = None
            if quote_data.get('lp') and data.get('lot_size'):
                # This is a rough approximation
                market_cap = (quote_data['lp'] * data.get('lot_size', 1)) / 10000000  # In crores
            
            return {
                'symbol': symbol,
                'name': data.get('description', symbol),
                'sector': data.get('sector', 'Unknown'),
                'industry': data.get('industry', 'Unknown'),
                'market_cap': market_cap,
                'exchange': data.get('exchange', 'NSE'),
                'instrument_type': data.get('instrument_type', 'EQ'),
                'lot_size': data.get('lot_size', 1),
                'tick_size': data.get('tick_size', 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """Get historical data from Fyers"""
        try:
            fyers_symbol = self.normalize_symbol(symbol)
            
            # Convert interval to Fyers format
            interval_mapping = {
                '1D': 'D',
                '1H': '60',
                '15M': '15',
                '5M': '5',
                '1M': '1'
            }
            
            fyers_interval = interval_mapping.get(interval, 'D')
            
            # Convert dates to timestamps
            start_timestamp = int(start_date.strftime('%s'))
            end_timestamp = int(end_date.strftime('%s'))
            
            params = {
                'symbol': fyers_symbol,
                'resolution': fyers_interval,
                'date_format': '1',
                'range_from': start_timestamp,
                'range_to': end_timestamp,
                'cont_flag': '1'
            }
            
            response = self._make_request('GET', '/api/v3/data/history', params=params)
            
            if not response or response.get('code') != 200:
                self.logger.warning(f"No historical data for {symbol}")
                return None
            
            candles = response.get('candles', [])
            if not candles:
                return None
            
            # Convert to DataFrame
            df_data = []
            for candle in candles:
                df_data.append({
                    'date': pd.to_datetime(candle[0], unit='s').date(),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': int(candle[5]) if len(candle) > 5 else 0
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('date').reset_index(drop=True)
            
            self.logger.info(f"Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time quotes from Fyers"""
        try:
            # Convert symbols to Fyers format
            fyers_symbols = [self.normalize_symbol(symbol) for symbol in symbols]
            
            # Fyers allows up to 50 symbols per request
            if len(fyers_symbols) > 50:
                self.logger.warning("Too many symbols, taking first 50")
                fyers_symbols = fyers_symbols[:50]
                symbols = symbols[:50]
            
            params = {
                'symbols': ','.join(fyers_symbols)
            }
            
            response = self._make_request('GET', '/api/v3/data/quotes', params=params)
            
            if not response or response.get('code') != 200:
                return None
            
            quotes = response.get('d', [])
            if not quotes:
                return None
            
            result = {}
            for i, quote in enumerate(quotes):
                if i < len(symbols):
                    symbol = symbols[i]
                    result[symbol] = {
                        'symbol': symbol,
                        'ltp': quote.get('lp', 0),  # Last price
                        'open': quote.get('o', 0),
                        'high': quote.get('h', 0),
                        'low': quote.get('l', 0),
                        'close': quote.get('c', 0),  # Previous close
                        'volume': quote.get('v', 0),
                        'change': quote.get('ch', 0),
                        'change_percent': quote.get('chp', 0),
                        'timestamp': datetime.now()
                    }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting real-time data: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks (Fyers doesn't have direct search, return empty)"""
        # Fyers doesn't provide a direct search API
        # This would typically require loading the complete symbol master
        self.logger.info(f"Search not directly supported by Fyers API")
        return []
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status from Fyers"""
        try:
            response = self._make_request('GET', '/api/v3/data/market-status')
            
            if response and response.get('code') == 200:
                return response.get('data', {})
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return {}
    
    def get_available_symbols(self, exchange: str = 'NSE') -> List[str]:
        """Get list of available symbols (requires symbol master file)"""
        # This would typically require downloading and parsing the symbol master file
        # For now, return a basic list of major stocks
        
        major_stocks = [
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR',
            'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'ASIANPAINT',
            'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND',
            'BAJFINANCE', 'M&M', 'TECHM', 'HCLTECH', 'WIPRO', 'NTPC'
        ]
        
        return major_stocks