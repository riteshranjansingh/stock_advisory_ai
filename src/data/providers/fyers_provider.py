"""
Fyers Data Provider - Updated with New Authentication System
Implementation for Fyers broker API using professional authentication
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
    """Fyers broker data provider with integrated authentication"""
    
    def __init__(self):
        super().__init__("Fyers", DataProviderPriority.PRIMARY)
        
        # Fyers API settings
        self.base_url = "https://api-t1.fyers.in"
        self.api_version = "v3"
        self.access_token = None
        self.client_id = None
        self.fyers_client = None
        
        # Authentication system
        self.authenticator = None
        
        # Rate limiting settings for Fyers
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.daily_request_limit = 2000  # Fyers limit
        
        # Indian market symbols format for Fyers
        self.exchange_mapping = {
            'NSE': 'NSE',
            'BSE': 'BSE'
        }
        
        self.logger.info("Fyers provider initialized with new authentication system")
    
    def authenticate(self, credentials: Dict[str, str] = None) -> bool:
        """
        Authenticate with Fyers API using the new authentication system
        
        Args:
            credentials: Optional - Not used anymore, authentication is automatic
        """
        try:
            # Import here to avoid circular imports
            from src.auth.fyers_auth import FyersAuthenticator
            
            self.logger.info("Starting Fyers authentication...")
            
            # Create authenticator
            self.authenticator = FyersAuthenticator()
            
            # Get access token (handles existing token or new authentication)
            self.access_token = self.authenticator.get_access_token()
            
            if not self.access_token:
                raise AuthenticationError(self.name, "Failed to obtain access token")
            
            # Get client ID from authenticator
            self.client_id = self.authenticator.credentials.get('CLIENT_ID')
            
            if not self.client_id:
                raise AuthenticationError(self.name, "Client ID not available")
            
            # Get authenticated Fyers client
            self.fyers_client = self.authenticator.get_authenticated_client()
            
            if not self.fyers_client:
                raise AuthenticationError(self.name, "Failed to create Fyers client")
            
            # Test authentication with profile API
            profile_response = self.fyers_client.get_profile()
            
            if profile_response and profile_response.get('s') == 'ok':
                self.status = DataProviderStatus.ACTIVE
                self.logger.info("✅ Fyers authentication successful!")
                self.logger.info(f"Connected as: {profile_response.get('data', {}).get('name', 'Unknown')}")
                return True
            else:
                error_msg = profile_response.get('message', 'Authentication test failed') if profile_response else 'No response'
                raise AuthenticationError(self.name, error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ Fyers authentication failed: {e}")
            self.status = DataProviderStatus.ERROR
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication"""
        if not self.fyers_client or not self.access_token:
            self.logger.info("No authentication found, attempting to authenticate...")
            return self.authenticate()
        
        # Check if token is still valid
        if self.authenticator and not self.authenticator.is_token_valid():
            self.logger.info("Token expired, re-authenticating...")
            return self.authenticate()
        
        return True
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to Fyers API"""
        if not self._ensure_authenticated():
            raise AuthenticationError(self.name, "Authentication required")
        
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
                # Token might have expired, try to re-authenticate
                self.logger.warning("Token expired, attempting re-authentication...")
                if self.authenticate():
                    # Retry the request with new token
                    headers['Authorization'] = f"{self.client_id}:{self.access_token}"
                    response = requests.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=data,
                        timeout=30
                    )
                else:
                    raise AuthenticationError(self.name, "Re-authentication failed")
            
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
            if not self._ensure_authenticated():
                return None
            
            fyers_symbol = self.normalize_symbol(symbol)
            
            # Use Fyers client for quotes with correct format
            data_params = {'symbols': fyers_symbol}
            response = self.fyers_client.quotes(data=data_params)
            
            self.logger.debug(f"Stock info response for {symbol}: {response}")
            
            if not response or response.get('s') != 'ok':
                self.logger.warning(f"No stock info for {symbol}: {response}")
                return None
            
            quotes = response.get('d', [])
            if not quotes:
                return None
            
            quote_data = quotes[0]
            
            # Handle nested 'v' structure if present
            if 'v' in quote_data:
                quote_data = quote_data['v']
            
            # Calculate approximate market cap if possible
            market_cap = None
            if quote_data.get('lp'):  # Last price
                # This is very approximate without actual share count
                market_cap = quote_data['lp'] * 1000000  # Rough estimate in crores
            
            return {
                'symbol': symbol,
                'name': quote_data.get('n', symbol),  # Name if available
                'sector': 'Unknown',  # Fyers doesn't provide sector in quotes
                'industry': 'Unknown',
                'market_cap': market_cap,
                'exchange': 'NSE',
                'instrument_type': 'EQ',
                'lot_size': 1,
                'tick_size': 0.05,
                'last_price': quote_data.get('lp', 0),
                'change': quote_data.get('ch', 0),
                'change_percent': quote_data.get('chp', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """Get historical data from Fyers"""
        try:
            if not self._ensure_authenticated():
                return None
            
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
            
            # Convert dates to Unix timestamps
            start_timestamp = int(time.mktime(start_date.timetuple()))
            end_timestamp = int(time.mktime(end_date.timetuple()))
            
            # Correct Fyers API format
            data_params = {
                'symbol': fyers_symbol,
                'resolution': fyers_interval,
                'date_format': '0',  # Use 0 for Unix timestamps
                'range_from': str(start_timestamp),
                'range_to': str(end_timestamp),
                'cont_flag': '1'
            }
            
            self.logger.debug(f"Historical data request: {data_params}")
            
            response = self.fyers_client.history(data=data_params)
            
            self.logger.debug(f"Historical data response: {response}")
            
            if not response or response.get('s') != 'ok':
                self.logger.warning(f"No historical data for {symbol}: {response}")
                return None
            
            candles = response.get('candles', [])
            if not candles:
                self.logger.warning(f"No candle data for {symbol}")
                return None
            
            # Convert to DataFrame
            df_data = []
            for candle in candles:
                if len(candle) >= 6:  # Ensure we have all OHLCV data
                    df_data.append({
                        'date': pd.to_datetime(candle[0], unit='s').date(),
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': int(candle[5])
                    })
            
            if not df_data:
                self.logger.warning(f"No valid candle data for {symbol}")
                return None
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('date').reset_index(drop=True)
            
            self.logger.info(f"✅ Retrieved {len(df)} records for {symbol} from {start_date} to {end_date}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error getting historical data for {symbol}: {e}")
            return None
    
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time quotes from Fyers"""
        try:
            if not self._ensure_authenticated():
                return None
            
            # Convert symbols to Fyers format
            fyers_symbols = [self.normalize_symbol(symbol) for symbol in symbols]
            
            # Fyers allows multiple symbols in comma-separated format
            if len(fyers_symbols) > 50:
                self.logger.warning("Too many symbols, taking first 50")
                fyers_symbols = fyers_symbols[:50]
                symbols = symbols[:50]
            
            # Correct Fyers API format for quotes
            symbols_str = ','.join(fyers_symbols)
            data_params = {'symbols': symbols_str}
            
            self.logger.debug(f"Real-time data request: {data_params}")
            
            response = self.fyers_client.quotes(data=data_params)
            
            self.logger.debug(f"Real-time data response: {response}")
            
            if not response or response.get('s') != 'ok':
                self.logger.warning(f"Failed to get real-time data: {response}")
                return None
            
            quotes = response.get('d', [])
            if not quotes:
                self.logger.warning("No quotes data received")
                return None
            
            result = {}
            for i, quote in enumerate(quotes):
                if i < len(symbols):
                    symbol = symbols[i]
                    
                    # Handle nested 'v' structure if present
                    quote_data = quote.get('v', quote) if 'v' in quote else quote
                    
                    result[symbol] = {
                        'symbol': symbol,
                        'ltp': quote_data.get('lp', 0),  # Last price
                        'open': quote_data.get('o', 0),
                        'high': quote_data.get('h', 0),
                        'low': quote_data.get('l', 0),
                        'close': quote_data.get('c', 0),  # Previous close
                        'volume': quote_data.get('v', 0),
                        'change': quote_data.get('ch', 0),
                        'change_percent': quote_data.get('chp', 0),
                        'timestamp': datetime.now()
                    }
            
            self.logger.info(f"✅ Retrieved real-time data for {len(result)} symbols")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error getting real-time data: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks (basic implementation)"""
        # For now, return a filtered list of major stocks
        major_stocks_info = [
            {'symbol': 'RELIANCE', 'name': 'Reliance Industries Ltd', 'sector': 'Energy'},
            {'symbol': 'TCS', 'name': 'Tata Consultancy Services Ltd', 'sector': 'IT'},
            {'symbol': 'INFY', 'name': 'Infosys Ltd', 'sector': 'IT'},
            {'symbol': 'HDFCBANK', 'name': 'HDFC Bank Ltd', 'sector': 'Banking'},
            {'symbol': 'ICICIBANK', 'name': 'ICICI Bank Ltd', 'sector': 'Banking'},
            {'symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever Ltd', 'sector': 'FMCG'},
            {'symbol': 'ITC', 'name': 'ITC Ltd', 'sector': 'FMCG'},
            {'symbol': 'SBIN', 'name': 'State Bank of India', 'sector': 'Banking'},
            {'symbol': 'BHARTIARTL', 'name': 'Bharti Airtel Ltd', 'sector': 'Telecom'},
            {'symbol': 'KOTAKBANK', 'name': 'Kotak Mahindra Bank Ltd', 'sector': 'Banking'}
        ]
        
        query_lower = query.lower()
        filtered_stocks = [
            stock for stock in major_stocks_info 
            if query_lower in stock['symbol'].lower() or query_lower in stock['name'].lower()
        ]
        
        return filtered_stocks[:10]  # Return top 10 matches
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status from Fyers"""
        try:
            if not self._ensure_authenticated():
                return {}
            
            # Fyers doesn't have a direct market status API
            # We can infer from current time and market hours
            now = datetime.now()
            
            # NSE market hours: 9:15 AM to 3:30 PM IST
            market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
            
            is_open = (
                now.weekday() < 5 and  # Monday to Friday
                market_open_time <= now <= market_close_time
            )
            
            return {
                'market_status': 'OPEN' if is_open else 'CLOSED',
                'timestamp': now,
                'next_open': market_open_time + timedelta(days=1) if not is_open else None,
                'next_close': market_close_time if is_open else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return {}
    
    def get_available_symbols(self, exchange: str = 'NSE') -> List[str]:
        """Get list of available symbols"""
        # Return expanded list of major Indian stocks
        major_stocks = [
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR',
            'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'ASIANPAINT',
            'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND',
            'BAJFINANCE', 'M&M', 'TECHM', 'HCLTECH', 'WIPRO', 'NTPC',
            'ONGC', 'POWERGRID', 'TATASTEEL', 'JSWSTEEL', 'COALINDIA',
            'DRREDDY', 'CIPLA', 'BAJAJFINSV', 'HEROMOTOCO', 'EICHERMOT',
            'BRITANNIA', 'DABUR', 'GODREJCP', 'MARICO', 'COLPAL',
            'APOLLOHOSP', 'FORTIS', 'MAXHEALTH', 'HDFCLIFE', 'SBILIFE'
        ]
        
        return major_stocks
    
    def test_connection(self) -> bool:
        """Test connection with Fyers API"""
        try:
            if not self._ensure_authenticated():
                return False
            
            # Test with a simple profile call
            profile = self.fyers_client.get_profile()
            return profile and profile.get('s') == 'ok'
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False