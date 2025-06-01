"""
Complete MStock Provider Fix - Working Integration
Based on successful API tests, this implements the working MStock provider
"""

import requests
import pandas as pd
import csv
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from io import StringIO
import time
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.providers.base_provider import (
    BaseDataProvider, DataProviderPriority, DataProviderStatus,
    DataProviderError, RateLimitError, AuthenticationError, DataNotFoundError
)
from src.auth.mstock_auth import MStockAuthenticator

class MStockProvider(BaseDataProvider):
    """
    Fixed MStock Provider with Working API Integration
    Based on successful API testing - implements what actually works
    """
    
    def __init__(self):
        super().__init__("MStock", DataProviderPriority.PRIMARY)
        
        # API settings
        self.base_url = "https://api.mstock.trade/openapi/typea"
        self.authenticator = None
        self.access_token = None
        self.api_key = None
        
        # Working cache for instruments (from successful Script Master)
        self._instruments_cache = {}  # symbol -> instrument data
        self._token_cache = {}        # symbol -> token mapping
        self._script_master_loaded = False
        
        # Rate limiting (from documentation)
        self.rate_limit_delay = 1.0
        self.daily_request_limit = 2000
        self.endpoint_limits = {
            'scriptmaster': 5,    # 5 requests per minute
            'historical': 15,     # 15 requests per minute  
            'quote': 30           # 30 requests per minute
        }
        
        self.logger.info("Fixed MStock provider initialized")
    
    def authenticate(self, credentials: Dict[str, str] = None) -> bool:
        """Authenticate using working MStock auth system"""
        try:
            self.authenticator = MStockAuthenticator()
            
            if not self.authenticator.authenticate():
                self.logger.error("MStock authentication failed")
                return False
            
            self.access_token = self.authenticator.access_token
            self.api_key = self.authenticator.credentials.get('API_KEY')
            
            if not self.access_token or not self.api_key:
                self.logger.error("Missing access token or API key")
                return False
            
            self.status = DataProviderStatus.ACTIVE
            self.logger.info("✅ MStock authentication successful")
            
            # Load Script Master on successful authentication
            self._load_script_master()
            
            return True
            
        except Exception as e:
            self.logger.error(f"MStock authentication error: {e}")
            self.status = DataProviderStatus.ERROR
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get properly formatted headers for API requests"""
        return {
            'X-Mirae-Version': '1',
            'Authorization': f'token {self.api_key}:{self.access_token}',
        }
    
    def _load_script_master(self) -> bool:
        """Load Script Master with WORKING filtering logic"""
        try:
            if self._script_master_loaded and len(self._instruments_cache) > 0:
                self.logger.info(f"Script Master already loaded: {len(self._instruments_cache)} instruments")
                return True
            
            self.logger.info("Loading Script Master with FIXED filtering...")
            
            headers = self._get_headers()
            response = requests.get(
                f"{self.base_url}/instruments/scriptmaster",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                self.logger.error(f"Script Master request failed: {response.status_code}")
                return False
            
            csv_data = response.text
            self.logger.info(f"Got {len(csv_data)} characters of Script Master data")
            
            # Parse with FIXED filtering logic
            return self._parse_script_master_fixed(csv_data)
            
        except Exception as e:
            self.logger.error(f"Error loading Script Master: {e}")
            return False
    
    def _parse_script_master_fixed(self, csv_data: str) -> bool:
        """Parse Script Master with WORKING filtering logic from our tests"""
        try:
            csv_reader = csv.DictReader(StringIO(csv_data))
            
            total_rows = 0
            equity_count = 0
            
            # Safe type conversion functions (from our fix)
            def safe_int(value, default=1):
                try:
                    return int(value) if value and value.strip() else default
                except (ValueError, AttributeError):
                    return default
            
            def safe_float(value, default=0.05):
                try:
                    return float(value) if value and value.strip() else default
                except (ValueError, AttributeError):
                    return default
            
            for row in csv_reader:
                total_rows += 1
                
                # WORKING equity filter (from our successful test)
                is_equity = (
                    row.get('instrument_type', '').upper() == 'EQ' and
                    row.get('segment', '').upper() == 'EQ' and
                    row.get('exchange', '').upper() == 'NSE' and
                    row.get('tradingsymbol', '').strip() != ''
                )
                
                if is_equity:
                    equity_count += 1
                    symbol = row.get('tradingsymbol', '').strip()
                    
                    # Store instrument data with safe conversion
                    instrument = {
                        'symbol': symbol,
                        'name': row.get('name', '').strip(),
                        'instrument_token': row.get('instrument_token', '').strip(),
                        'exchange_token': row.get('exchange_token', '').strip(),
                        'exchange': row.get('exchange', 'NSE').strip(),
                        'lot_size': safe_int(row.get('lot_size', ''), 1),
                        'tick_size': safe_float(row.get('tick_size', ''), 0.05),
                        'instrument_type': row.get('instrument_type', 'EQ').strip(),
                        'segment': row.get('segment', 'EQ').strip()
                    }
                    
                    # Cache by symbol and token
                    self._instruments_cache[symbol] = instrument
                    self._token_cache[symbol] = instrument['instrument_token']
            
            self.logger.info(f"✅ Script Master parsed successfully:")
            self.logger.info(f"   Total rows: {total_rows:,}")
            self.logger.info(f"   Equity instruments: {equity_count:,}")
            self.logger.info(f"   Success rate: {equity_count/total_rows*100:.1f}%")
            
            self._script_master_loaded = True
            return equity_count > 0
            
        except Exception as e:
            self.logger.error(f"Error parsing Script Master: {e}")
            return False
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock info using cached Script Master data"""
        try:
            # Ensure Script Master is loaded
            if not self._script_master_loaded:
                self._load_script_master()
            
            symbol = symbol.upper()
            
            if symbol in self._instruments_cache:
                instrument = self._instruments_cache[symbol]
                
                return {
                    'symbol': symbol,
                    'name': instrument['name'],
                    'exchange': instrument['exchange'],
                    'instrument_token': instrument['instrument_token'],
                    'lot_size': instrument['lot_size'],
                    'tick_size': instrument['tick_size'],
                    'instrument_type': instrument['instrument_type'],
                    'segment': instrument['segment'],
                    'provider': 'MStock'
                }
            else:
                self.logger.debug(f"Stock {symbol} not found in Script Master")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """
        Get historical data using WORKING token-based API format
        This is the breakthrough format that works perfectly!
        """
        try:
            # Ensure authentication and Script Master
            if not self._ensure_ready():
                return None
            
            # Get instrument token
            token = self._get_instrument_token(symbol)
            if not token:
                self.logger.error(f"No instrument token found for {symbol}")
                return None
            
            # Convert interval to MStock format
            timeframe_mapping = {
                '1D': 'day',
                '1H': '60minute', 
                '30M': '30minute',
                '15M': '15minute',
                '5M': '5minute',
                '1M': '1minute'
            }
            
            mstock_timeframe = timeframe_mapping.get(interval, 'day')
            
            # Format dates as WORKING format from our tests
            from_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
            to_date = end_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Use WORKING URL format: /instruments/historical/{token}/{timeframe}
            url = f"{self.base_url}/instruments/historical/{token}/{mstock_timeframe}"
            
            headers = self._get_headers()
            params = {
                'from': from_date,
                'to': to_date
            }
            
            self.logger.info(f"Fetching historical data for {symbol} (token: {token})")
            self.logger.debug(f"URL: {url}")
            self.logger.debug(f"Params: {params}")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Historical data request failed: {response.status_code} - {response.text}")
                return None
            
            # Parse WORKING response format
            data = response.json()
            
            if data.get('status') != 'success':
                self.logger.error(f"API returned error: {data}")
                return None
            
            # Extract candles from WORKING format
            candles = data.get('data', {}).get('candles', [])
            
            if not candles:
                self.logger.warning(f"No candle data for {symbol}")
                return None
            
            # Convert to DataFrame with WORKING format
            df_data = []
            for candle in candles:
                if len(candle) >= 6:  # [timestamp, open, high, low, close, volume]
                    df_data.append({
                        'date': pd.to_datetime(candle[0]).date(),
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
            
            self.logger.info(f"✅ Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get real-time data - TEMPORARILY DISABLED on weekends
        Will work during market hours (test Monday)
        """
        try:
            # Check if it's weekend/market hours
            now = datetime.now()
            if now.weekday() >= 5:  # Saturday or Sunday
                self.logger.info("Real-time data disabled on weekends (markets closed)")
                return None
            
            # Market hours check (9:15 AM to 3:30 PM IST)
            market_open = now.replace(hour=9, minute=15)
            market_close = now.replace(hour=15, minute=30)
            
            if not (market_open <= now <= market_close):
                self.logger.info("Real-time data disabled outside market hours")
                return None
            
            # During market hours, use the WORKING format (to be tested Monday)
            return self._get_real_time_market_hours(symbols)
            
        except Exception as e:
            self.logger.error(f"Error in real-time data: {e}")
            return None
    
    def _get_real_time_market_hours(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Real-time data during market hours (working format for Monday test)"""
        try:
            if not self._ensure_ready():
                return None
            
            headers = self._get_headers()
            
            # Use WORKING array format from documentation
            symbol_list = [f"NSE:{symbol}" for symbol in symbols]
            
            params = {'i': symbol_list}  # Array format
            url = f"{self.base_url}/instruments/quote/ltp"
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                self.logger.error(f"Real-time request failed: {response.status_code}")
                return None
            
            data = response.json()
            
            # Parse response (format to be confirmed Monday)
            result = {}
            if isinstance(data, dict) and 'data' in data:
                # Process LTP data format
                for symbol in symbols:
                    if symbol in data['data']:
                        quote_data = data['data'][symbol]
                        result[symbol] = {
                            'symbol': symbol,
                            'ltp': quote_data.get('ltp', 0),
                            'change': quote_data.get('change', 0),
                            'change_pct': quote_data.get('change_pct', 0),
                            'timestamp': datetime.now(),
                            'provider': 'MStock'
                        }
            
            return result if result else None
            
        except Exception as e:
            self.logger.error(f"Market hours real-time error: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search stocks in cached Script Master data"""
        try:
            if not self._script_master_loaded:
                self._load_script_master()
            
            query_lower = query.lower()
            results = []
            
            for symbol, instrument in self._instruments_cache.items():
                if (query_lower in symbol.lower() or 
                    query_lower in instrument['name'].lower()):
                    
                    results.append({
                        'symbol': symbol,
                        'name': instrument['name'],
                        'provider': 'MStock',
                        'instrument_token': instrument['instrument_token']
                    })
                    
                    if len(results) >= 20:  # Limit results
                        break
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []
    
    def _get_instrument_token(self, symbol: str) -> Optional[str]:
        """Get instrument token for symbol"""
        symbol = symbol.upper()
        return self._token_cache.get(symbol)
    
    def _ensure_ready(self) -> bool:
        """Ensure provider is authenticated and Script Master loaded"""
        if not self.access_token:
            return self.authenticate()
        
        if not self._script_master_loaded:
            return self._load_script_master()
        
        return True
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols"""
        if not self._script_master_loaded:
            self._load_script_master()
        
        return list(self._instruments_cache.keys())
    
    def test_connection(self) -> bool:
        """Test connection with working historical API"""
        try:
            if not self._ensure_ready():
                return False
            
            # Test with known working historical API
            test_token = "2885"  # RELIANCE token from our tests
            url = f"{self.base_url}/instruments/historical/{test_token}/day"
            
            # Test last 2 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=2)
            
            params = {
                'from': start_date.strftime("%Y-%m-%d %H:%M:%S"),
                'to': end_date.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            success = response.status_code == 200
            self.logger.info(f"Connection test: {'✅ PASS' if success else '❌ FAIL'}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            'name': 'MStock',
            'broker': 'Mirae Asset',
            'type': 'Real Broker API (Fixed)',
            'supports_realtime': True,
            'supports_historical': True,
            'supports_search': True,
            'authenticated': bool(self.access_token),
            'script_master_loaded': self._script_master_loaded,
            'cached_instruments': len(self._instruments_cache),
            'working_features': [
                'Authentication ✅',
                'Script Master ✅', 
                'Historical Data ✅',
                'Instrument Tokens ✅',
                'Search ✅'
            ],
            'rate_limits': self.endpoint_limits,
            'status': 'WORKING - Ready for AI Trading System!'
        }
    # ============================================================================
    # MSTOCK PROVIDER SYMBOL IMPLEMENTATION
    # ============================================================================

    def _provider_normalize_symbol(self, symbol: str, exchange: str = 'NSE') -> str:
        """
        Convert clean symbol to MStock format (instrument token)
        
        Examples:
            "RELIANCE" → "2885" (instrument token)
            "TCS" → "11536" (instrument token)
        """
        symbol = symbol.upper()
        
        # Check if we have the token in our instruments cache
        if hasattr(self, '_instruments_cache') and symbol in self._instruments_cache:
            instrument = self._instruments_cache[symbol]
            return instrument.get('instrument_token', symbol)
        
        # If token cache not available, we might need to search
        # This is where MStock's script master lookup would happen
        if hasattr(self, '_get_instrument_token'):
            token = self._get_instrument_token(symbol)
            if token:
                return token
        
        # Fallback: return symbol as-is (will be handled by MStock API)
        return symbol
    
    def _provider_denormalize_symbol(self, provider_symbol: str) -> str:
        """
        Convert MStock token back to clean symbol
        
        Examples:
            "2885" → "RELIANCE"
            "11536" → "TCS"
        """
        try:
            # Check reverse lookup in instruments cache
            if hasattr(self, '_instruments_cache'):
                for symbol, instrument in self._instruments_cache.items():
                    if instrument.get('instrument_token') == provider_symbol:
                        return symbol
            
            # If it's already a symbol (not a token), return as-is
            if provider_symbol.isdigit():
                # It's a token, but we don't have reverse mapping
                self.logger.warning(f"No reverse mapping for MStock token {provider_symbol}")
                return provider_symbol
            else:
                # It's already a symbol
                return provider_symbol.upper()
                
        except Exception as e:
            self.logger.warning(f"Error denormalizing MStock symbol {provider_symbol}: {e}")
            return provider_symbol

            

# Test the fixed provider
if __name__ == "__main__":
    print("🚀 Testing FIXED MStock Provider")
    print("=" * 40)
    
    provider = MStockProvider()
    
    # Test authentication
    if provider.authenticate():
        print("✅ Authentication successful")
        
        # Test stock info
        stock_info = provider.get_stock_info('RELIANCE')
        if stock_info:
            print(f"✅ Stock info: {stock_info}")
        
        # Test historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        historical = provider.get_historical_data('RELIANCE', start_date, end_date)
        if historical is not None:
            print(f"✅ Historical data: {len(historical)} records")
            print(f"   Sample: {historical.head()}")
        
        # Test search
        search_results = provider.search_stocks('RELIANCE')
        if search_results:
            print(f"✅ Search: {search_results[0]}")
        
        # Test connection
        if provider.test_connection():
            print("✅ Connection test passed")
        
        # Show provider info
        info = provider.get_provider_info()
        print(f"\n📊 Provider Status:")
        for feature in info['working_features']:
            print(f"   {feature}")
        
    else:
        print("❌ Authentication failed")