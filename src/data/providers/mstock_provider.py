"""
MStock Data Provider - Market Data from Mirae Asset API

Implementation for MStock broker API using Script Master and correct API patterns.
Supports real-time quotes, historical data, stock search, and market data.
"""

import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import time
import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from .base_provider import (
    BaseDataProvider, DataProviderPriority, DataProviderStatus,
    DataProviderError, RateLimitError, AuthenticationError, DataNotFoundError
)

class MStockProvider(BaseDataProvider):
    """MStock broker data provider with Script Master integration"""
    
    def __init__(self):
        super().__init__("MStock", DataProviderPriority.PRIMARY)
        
        # MStock API settings
        self.base_url = "https://api.mstock.trade/openapi/typea"
        self.authenticator = None
        self.access_token = None
        self.api_key = None
        
        # Enhanced rate limiting settings (from working implementation guide)
        self.rate_limit_delay = 1.0
        self.daily_request_limit = 2000
        self.endpoint_limits = {
            'scriptmaster': 5,      # Only 5 requests per minute for script master
            'historical': 15,       # 15 requests per minute for historical data
            'quote': 30,           # 30 requests per minute for quotes
            'orders': 20           # 20 requests per minute for orders
        }
        
        # Script Master cache (ESSENTIAL for MStock API)
        self._script_master_cache = {}
        self._instrument_tokens = {}
        self._last_script_master_fetch = None
        self._script_master_cache_duration = 3600  # 1 hour cache
        self._script_master_loading = False  # Prevent multiple simultaneous loads
        
        self.logger.info("MStock provider initialized with Script Master caching")
    
    def authenticate(self, credentials: Dict[str, str] = None) -> bool:
        """Authenticate with MStock API using the authentication system with auto-retry"""
        try:
            # Import here to avoid circular imports
            from src.auth.mstock_auth import MStockAuthenticator
            
            self.logger.info("Starting MStock authentication...")
            
            # Create authenticator
            self.authenticator = MStockAuthenticator()
            
            # Get access token (handles existing token or new authentication)
            self.access_token = self.authenticator.get_access_token()
            
            if not self.access_token:
                raise AuthenticationError(self.name, "Failed to obtain access token")
            
            # Get API key from authenticator
            self.api_key = self.authenticator.credentials.get('API_KEY')
            
            if not self.api_key:
                raise AuthenticationError(self.name, "API key not available")
            
            # Test authentication with user fund summary (with auto-retry logic)
            test_success = self._test_authentication_with_retry()
            
            if test_success:
                self.status = DataProviderStatus.ACTIVE
                self.logger.info("✅ MStock authentication successful!")
                return True
            else:
                raise AuthenticationError(self.name, "Authentication test failed after retries")
                
        except Exception as e:
            self.logger.error(f"❌ MStock authentication failed: {e}")
            self.status = DataProviderStatus.ERROR
            return False
    
    def _test_authentication_with_retry(self, max_retries: int = 2) -> bool:
        """Test authentication with auto-retry on 401 errors"""
        for attempt in range(max_retries + 1):
            try:
                test_headers = self._get_headers('GET')
                test_response = requests.get(
                    f"{self.base_url}/user/fundsummary",
                    headers=test_headers,
                    timeout=30
                )
                
                if test_response.status_code == 200:
                    result = test_response.json()
                    if result.get('status') == 'success':
                        self.logger.info(f"✅ Authentication test successful (attempt {attempt + 1})")
                        return True
                    else:
                        error_msg = result.get('message', 'Authentication test failed')
                        self.logger.warning(f"Authentication test failed: {error_msg}")
                        return False
                
                elif test_response.status_code == 401 and attempt < max_retries:
                    # Token expired/invalid - try to get fresh token
                    self.logger.warning(f"❌ 401 error on attempt {attempt + 1}, retrying with fresh authentication...")
                    
                    # Force fresh authentication (bypass cache)
                    if self.authenticator:
                        # Clear the existing token to force fresh auth
                        self.authenticator.access_token = None
                        fresh_token = self.authenticator.authenticate()  # This will prompt for OTP if needed
                        
                        if fresh_token:
                            self.access_token = fresh_token
                            self.logger.info("✅ Obtained fresh token, retrying test...")
                            continue
                        else:
                            self.logger.error("❌ Failed to get fresh token")
                            return False
                    else:
                        return False
                else:
                    # Non-401 error or max retries reached
                    self.logger.error(f"❌ Authentication test failed: HTTP {test_response.status_code}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Authentication test error (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return False
        
        return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication"""
        if not self.access_token or not self.api_key:
            self.logger.info("No authentication found, attempting to authenticate...")
            return self.authenticate()
        
        # Check if token is still valid
        if self.authenticator and not self.authenticator.is_token_valid():
            self.logger.info("Token expired, re-authenticating...")
            return self.authenticate()
        
        return True
    
    def _get_headers(self, method: str = 'GET') -> Dict[str, str]:
        """Get headers for MStock API requests with correct Content-Type for method"""
        if not self.access_token or not self.api_key:
            raise AuthenticationError(self.name, "Missing authentication credentials")
        
        headers = {
            'X-Mirae-Version': '1',
            'Authorization': f'token {self.api_key}:{self.access_token}'
        }
        
        # Only add Content-Type for POST requests (as per MStock API docs)
        if method.upper() == 'POST':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, max_auth_retries: int = 1) -> Optional[Dict]:
        """Make HTTP request to MStock API with enhanced auto-retry logic"""
        if not self._ensure_authenticated():
            raise AuthenticationError(self.name, "Authentication required")
        
        if not self.check_rate_limit():
            raise RateLimitError(self.name)
        
        auth_attempts = 0
        
        while auth_attempts <= max_auth_retries:
            try:
                url = f"{self.base_url}{endpoint}"
                headers = self._get_headers(method)
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=30
                )
                
                self.record_request()
                
                # Handle rate limiting
                if response.status_code == 429:
                    raise RateLimitError(self.name)
                
                # Enhanced 401 handling with auto-retry
                if response.status_code == 401 and auth_attempts < max_auth_retries:
                    auth_attempts += 1
                    self.logger.warning(f"❌ 401 error (attempt {auth_attempts}), auto-retrying authentication...")
                    
                    # Clear existing token and force fresh authentication
                    if self.authenticator:
                        self.authenticator.access_token = None
                        fresh_token = self.authenticator.get_access_token()
                        
                        if fresh_token:
                            self.access_token = fresh_token
                            self.logger.info("✅ Auto-retry: Got fresh token, retrying request...")
                            continue  # Retry the request with new token
                        else:
                            self.logger.error("❌ Auto-retry: Failed to get fresh token")
                            break
                    else:
                        break
                
                elif response.status_code == 401:
                    # Max retries exhausted
                    self.logger.error("❌ Max authentication retries exhausted")
                    raise AuthenticationError(self.name, "Authentication failed after retries")
                
                if response.status_code == 200:
                    # Handle different content types
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'application/json' in content_type:
                        result = response.json()
                        
                        # Check MStock specific error responses
                        if result.get('status') == 'error':
                            error_type = result.get('error_type', 'Unknown')
                            error_msg = result.get('message', 'API error')
                            
                            if error_type in ['APIKeyException', 'TokenException']:
                                raise AuthenticationError(self.name, error_msg)
                            elif error_type == 'InputException':
                                raise DataProviderError(self.name, error_msg)
                            else:
                                raise DataProviderError(self.name, f"{error_type}: {error_msg}")
                        
                        return result
                    
                    elif 'text/csv' in content_type or endpoint == '/instruments/scriptmaster':
                        return response.text
                    
                    else:
                        try:
                            result = response.json()
                            
                            if result.get('status') == 'error':
                                error_type = result.get('error_type', 'Unknown')
                                error_msg = result.get('message', 'API error')
                                
                                if error_type in ['APIKeyException', 'TokenException']:
                                    raise AuthenticationError(self.name, error_msg)
                                elif error_type == 'InputException':
                                    raise DataProviderError(self.name, error_msg)
                                else:
                                    raise DataProviderError(self.name, f"{error_type}: {error_msg}")
                            
                            return result
                        except ValueError:
                            return response.text
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {response.text}")
                    raise DataProviderError(self.name, f"HTTP {response.status_code}")
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error: {e}")
                raise DataProviderError(self.name, str(e))
        
        # If we reach here, all retries failed
        raise AuthenticationError(self.name, "All authentication retries failed")
    
    def _ensure_script_master_loaded(self) -> bool:
        """Ensure Script Master is loaded and cached with proper rate limiting"""
        try:
            # Check if already loading (prevent multiple simultaneous calls)
            if self._script_master_loading:
                self.logger.info("Script Master loading in progress, waiting...")
                import time
                # Wait up to 30 seconds for loading to complete
                for _ in range(30):
                    time.sleep(1)
                    if not self._script_master_loading:
                        break
                # Return current state after waiting
                return len(self._instrument_tokens) > 0
            
            # Check if we need to refresh cache
            now = datetime.now()
            if (self._last_script_master_fetch and 
                (now - self._last_script_master_fetch).seconds < self._script_master_cache_duration and
                self._instrument_tokens):
                self.logger.debug("Using cached Script Master data")
                return True
            
            # Set loading flag to prevent concurrent calls
            self._script_master_loading = True
            
            try:
                self.logger.info("Fetching Script Master from MStock API (rate limited to 5/min)...")
                
                # Use correct endpoint from API guide
                response = self._make_request('GET', '/instruments/scriptmaster', max_auth_retries=0)
                
                if not response:
                    self.logger.error("Failed to fetch Script Master - no response")
                    return False
                
                csv_data = None
                if isinstance(response, dict):
                    if response.get('status') == 'success':
                        csv_data = response.get('data', '')
                    else:
                        error_msg = response.get('message', 'Unknown error')
                        self.logger.error(f"Script Master API error: {error_msg}")
                        return False
                elif isinstance(response, str):
                    csv_data = response
                else:
                    self.logger.error("Unexpected Script Master response format")
                    return False
                
                if not csv_data or len(csv_data.strip()) == 0:
                    self.logger.error("Empty Script Master data received")
                    return False
                
                # Parse the CSV data
                success = self._parse_script_master(csv_data)
                if success:
                    self._last_script_master_fetch = now
                    self.logger.info(f"✅ Script Master loaded: {len(self._instrument_tokens)} instruments cached")
                    return True
                else:
                    self.logger.error("Failed to parse Script Master data")
                    return False
                    
            finally:
                # Always clear the loading flag
                self._script_master_loading = False
                
        except Exception as e:
            self._script_master_loading = False
            self.logger.error(f"Error loading Script Master: {e}")
            return False
    
    def _parse_script_master(self, csv_data: str) -> bool:
        """Parse Script Master CSV and cache instrument tokens"""
        try:
            import csv
            import io
            
            # Clear existing caches
            self._script_master_cache.clear()
            self._instrument_tokens.clear()
            
            # Parse CSV data line by line to handle potential formatting issues
            lines = csv_data.strip().split('\n')
            if not lines:
                self.logger.error("No lines found in Script Master CSV")
                return False
            
            # Get header line
            header_line = lines[0]
            self.logger.debug(f"CSV Header: {header_line}")
            
            # Use csv.DictReader for robust parsing
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            
            parsed_count = 0
            equity_count = 0
            
            for row_num, row in enumerate(csv_reader):
                try:
                    # Extract key fields with case-insensitive handling
                    token = row.get('token') or row.get('Token') or row.get('TOKEN', '').strip()
                    symbol = row.get('symbol') or row.get('Symbol') or row.get('SYMBOL', '').strip().upper()
                    exchange = row.get('exchange') or row.get('Exchange') or row.get('EXCHANGE', '').strip().upper()
                    name = row.get('name') or row.get('Name') or row.get('NAME', '').strip()
                    instrument_type = row.get('instrument_type') or row.get('InstrumentType') or row.get('INSTRUMENT_TYPE', '').strip()
                    
                    parsed_count += 1
                    
                    # Skip if essential fields are missing
                    if not token or not symbol or not exchange:
                        continue
                    
                    # Focus on equity instruments from NSE/BSE
                    if exchange in ['NSE', 'BSE']:
                        # Accept various equity instrument types
                        if instrument_type in ['EQ', 'EQUITY', ''] or not instrument_type:
                            symbol_key = f"{exchange}:{symbol}"
                            
                            instrument_data = {
                                'token': token,
                                'symbol': symbol,
                                'exchange': exchange,
                                'name': name or symbol,
                                'instrument_type': instrument_type or 'EQ',
                                'lot_size': row.get('lot_size', '1'),
                                'tick_size': row.get('tick_size', '0.05')
                            }
                            
                            self._script_master_cache[symbol_key] = instrument_data
                            self._instrument_tokens[symbol] = token
                            equity_count += 1
                
                except Exception as row_error:
                    self.logger.debug(f"Skipping row {row_num}: {row_error}")
                    continue
            
            self.logger.info(f"✅ Parsed {parsed_count} total rows, cached {equity_count} equity instruments")
            
            if equity_count == 0:
                self.logger.error("No equity instruments found in Script Master")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error parsing Script Master CSV: {e}")
            return False
    
    def get_instrument_token(self, symbol: str, exchange: str = 'NSE') -> Optional[str]:
        """Get instrument token for a symbol using cached Script Master data"""
        try:
            # Only try to load Script Master if we don't have tokens cached
            if not self._instrument_tokens and not self._script_master_loading:
                if not self._ensure_script_master_loaded():
                    return None
            
            # Try with exchange prefix first
            symbol_key = f"{exchange}:{symbol.upper()}"
            if symbol_key in self._script_master_cache:
                return self._script_master_cache[symbol_key]['token']
            
            # Try without exchange prefix
            symbol_upper = symbol.upper()
            if symbol_upper in self._instrument_tokens:
                return self._instrument_tokens[symbol_upper]
            
            self.logger.warning(f"Instrument token not found for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting instrument token for {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock information from MStock using OHLC endpoint with correct format"""
        try:
            if not self._ensure_authenticated():
                return None
            
            # Use correct format: NSE:SYMBOL (not array)
            mstock_symbol = f"NSE:{symbol.upper()}"
            params = {'i': mstock_symbol}
            
            self.logger.debug(f"Fetching stock info for {symbol} with params: {params}")
            
            # Use max_auth_retries=0 to avoid recursive auth calls
            response = self._make_request('GET', '/instruments/quote/ohlc', params=params, max_auth_retries=0)
            
            if response and response.get('status') == 'success':
                data = response.get('data', {})
                self.logger.debug(f"OHLC response data keys: {list(data.keys())}")
                
                if mstock_symbol in data and data[mstock_symbol]:
                    quote_info = data[mstock_symbol]
                    
                    # Handle different response formats
                    if isinstance(quote_info, dict):
                        ohlc = quote_info.get('ohlc', {})
                        last_price = quote_info.get('last_price', 0)
                        
                        # Calculate change from previous close
                        prev_close = ohlc.get('close', 0) if isinstance(ohlc, dict) else 0
                        change = last_price - prev_close if prev_close > 0 else 0
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                        
                        return {
                            'symbol': symbol.upper(),
                            'name': symbol.upper(),  # MStock doesn't provide company name in basic quotes
                            'exchange': 'NSE',
                            'last_price': last_price,
                            'open': ohlc.get('open', 0) if isinstance(ohlc, dict) else 0,
                            'high': ohlc.get('high', 0) if isinstance(ohlc, dict) else 0,
                            'low': ohlc.get('low', 0) if isinstance(ohlc, dict) else 0,
                            'close': prev_close,
                            'change': change,
                            'change_percent': change_percent,
                            'instrument_token': quote_info.get('instrument_token', ''),
                            'provider': 'MStock'
                        }
                else:
                    self.logger.warning(f"No data found for symbol {mstock_symbol} in response")
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                self.logger.warning(f"OHLC request failed: {error_msg}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """Get historical data from MStock using Script Master tokens"""
        try:
            if not self._ensure_authenticated():
                return None
            
            self.logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            # Check if Script Master is already loaded to avoid rate limit issues
            if not self._instrument_tokens:
                self.logger.warning("Script Master not loaded, cannot fetch historical data")
                return None
            
            # Get instrument token from cached Script Master data
            instrument_token = self.get_instrument_token(symbol, 'NSE')
            
            if not instrument_token:
                self.logger.error(f"Could not find instrument token for {symbol}")
                return None
            
            self.logger.info(f"Using cached instrument token {instrument_token} for {symbol}")
            
            # Convert interval to MStock format
            interval_mapping = {
                '1D': 'day',
                '1H': '60minute', 
                '15M': '15minute',
                '5M': '5minute',
                '1M': 'minute'
            }
            
            mstock_interval = interval_mapping.get(interval, 'day')
            
            # Format dates for MStock API (from working guide)
            from_date = start_date.strftime('%Y-%m-%d %H:%M:%S').replace(' ', '+')
            to_date = end_date.strftime('%Y-%m-%d %H:%M:%S').replace(' ', '+')
            
            # Add market hours if not present
            if '+00:00:00' in from_date:
                from_date = from_date.replace('+00:00:00', '+09:15:00')
            if '+00:00:00' in to_date:
                to_date = to_date.replace('+00:00:00', '+15:30:00')
            
            # Fetch historical data using correct endpoint
            historical_endpoint = f'/instruments/historical/{instrument_token}/{mstock_interval}'
            historical_params = {
                'from': from_date,
                'to': to_date
            }
            
            self.logger.info(f"Fetching from: {historical_endpoint}")
            self.logger.debug(f"Parameters: {historical_params}")
            
            hist_response = self._make_request('GET', historical_endpoint, params=historical_params, max_auth_retries=0)
            
            if not hist_response or hist_response.get('status') != 'success':
                error_msg = hist_response.get('message', 'Unknown error') if hist_response else 'No response'
                self.logger.warning(f"Historical data request failed: {error_msg}")
                return None
            
            # Parse historical data
            candles_data = hist_response.get('data', {}).get('candles', [])
            
            if not candles_data:
                self.logger.warning(f"No historical candles found for {symbol}")
                return None
            
            # Convert to DataFrame
            historical_records = []
            for candle in candles_data:
                try:
                    if len(candle) >= 6:
                        # Parse timestamp
                        timestamp_str = candle[0]
                        if 'T' in timestamp_str:
                            date_part = timestamp_str.split('T')[0]
                            hist_date = pd.to_datetime(date_part).date()
                        else:
                            hist_date = pd.to_datetime(timestamp_str).date()
                        
                        historical_records.append({
                            'date': hist_date,
                            'open': float(candle[1]),
                            'high': float(candle[2]), 
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': int(candle[5]) if candle[5] else 0
                        })
                except (ValueError, IndexError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid candle data: {e}")
                    continue
            
            if not historical_records:
                self.logger.warning(f"No valid historical records for {symbol}")
                return None
            
            # Create DataFrame
            df = pd.DataFrame(historical_records)
            df = df.sort_values('date').reset_index(drop=True)
            df['symbol'] = symbol.upper()
            
            self.logger.info(f"✅ Retrieved {len(df)} historical records for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error getting historical data for {symbol}: {e}")
            return None
    
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time quotes from MStock using correct parameter format from API guide"""
        try:
            if not self._ensure_authenticated():
                return None
            
            result = {}
            
            # Convert symbols to correct MStock format: NSE:SYMBOL
            mstock_symbols = []
            for symbol in symbols:
                mstock_symbol = f"NSE:{symbol.upper()}"
                mstock_symbols.append(mstock_symbol)
            
            # Process in small batches to respect rate limits
            batch_size = 5  # Conservative batch size for testing
            
            for i in range(0, len(mstock_symbols), batch_size):
                batch_symbols = mstock_symbols[i:i + batch_size]
                original_batch = symbols[i:i + batch_size]
                
                try:
                    # CORRECT FORMAT from API guide: comma-separated string
                    symbols_string = ','.join(batch_symbols)
                    params = {'i': symbols_string}
                    
                    self.logger.debug(f"Fetching quotes with params: {params}")
                    self.logger.debug(f"Symbols string: '{symbols_string}'")
                    
                    # Use LTP endpoint as per API guide
                    response = self._make_request('GET', '/instruments/quote/ltp', params=params, max_auth_retries=0)
                    
                    if response and response.get('status') == 'success':
                        data = response.get('data', {})
                        self.logger.debug(f"Response data keys: {list(data.keys())}")
                        
                        # Parse response for each symbol
                        for j, mstock_symbol in enumerate(batch_symbols):
                            if mstock_symbol in data and data[mstock_symbol] is not None:
                                quote_info = data[mstock_symbol]
                                original_symbol = original_batch[j]
                                
                                # Handle both direct value and nested structure
                                if isinstance(quote_info, dict):
                                    ltp = quote_info.get('last_price', 0)
                                else:
                                    ltp = quote_info if isinstance(quote_info, (int, float)) else 0
                                
                                result[original_symbol] = {
                                    'symbol': original_symbol,
                                    'ltp': ltp,
                                    'timestamp': datetime.now(),
                                    'provider': 'MStock'
                                }
                                
                                self.logger.debug(f"Parsed {original_symbol}: ₹{ltp}")
                    else:
                        error_msg = response.get('message', 'Unknown error') if response else 'No response'
                        self.logger.warning(f"Batch failed: {error_msg}")
                    
                    # Rate limiting between batches
                    if i + batch_size < len(mstock_symbols):
                        time.sleep(self.rate_limit_delay)
                        
                except Exception as batch_error:
                    self.logger.warning(f"Batch error for symbols {batch_symbols}: {batch_error}")
                    continue
            
            if result:
                self.logger.info(f"✅ Retrieved real-time data for {len(result)}/{len(symbols)} symbols from MStock")
                return result
            else:
                self.logger.warning("No real-time data retrieved from MStock")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting real-time data from MStock: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks using Script Master data"""
        try:
            # Only try to load Script Master if we don't have it and not already loading
            if not self._instrument_tokens and not self._script_master_loading:
                if not self._ensure_script_master_loaded():
                    self.logger.info("Script Master not available, using fallback search")
                    return self._fallback_search_stocks(query)
            
            # If Script Master is available, use it
            if self._script_master_cache:
                query_lower = query.lower()
                results = []
                
                # Search through cached Script Master data
                for symbol_key, instrument_data in self._script_master_cache.items():
                    symbol = instrument_data['symbol']
                    name = instrument_data.get('name', symbol)
                    
                    # Search by symbol or name
                    if (query_lower in symbol.lower() or 
                        query_lower in name.lower()):
                        
                        results.append({
                            'symbol': symbol,
                            'name': name,
                            'exchange': instrument_data['exchange'],
                            'instrument_token': instrument_data['token'],
                            'instrument_type': instrument_data.get('instrument_type', 'EQ'),
                            'provider': 'MStock'
                        })
                    
                    # Limit results
                    if len(results) >= 20:
                        break
                
                # Sort by relevance (exact matches first)
                results.sort(key=lambda x: (
                    0 if query_lower == x['symbol'].lower() else
                    1 if query_lower in x['symbol'].lower() else 2
                ))
                
                return results[:10]  # Return top 10 matches
            else:
                # Fallback if Script Master cache is empty
                return self._fallback_search_stocks(query)
            
        except Exception as e:
            self.logger.error(f"Stock search error for '{query}': {e}")
            return self._fallback_search_stocks(query)
    
    def _fallback_search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Fallback search method when Script Master is not available"""
        major_stocks = [
            {'symbol': 'RELIANCE', 'name': 'Reliance Industries Ltd'},
            {'symbol': 'TCS', 'name': 'Tata Consultancy Services Ltd'},
            {'symbol': 'INFY', 'name': 'Infosys Ltd'},
            {'symbol': 'HDFCBANK', 'name': 'HDFC Bank Ltd'},
            {'symbol': 'ICICIBANK', 'name': 'ICICI Bank Ltd'},
            {'symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever Ltd'},
            {'symbol': 'ITC', 'name': 'ITC Ltd'},
            {'symbol': 'SBIN', 'name': 'State Bank of India'},
            {'symbol': 'BHARTIARTL', 'name': 'Bharti Airtel Ltd'},
            {'symbol': 'KOTAKBANK', 'name': 'Kotak Mahindra Bank Ltd'}
        ]
        
        query_lower = query.lower()
        filtered_stocks = [
            stock for stock in major_stocks 
            if query_lower in stock['symbol'].lower() or query_lower in stock['name'].lower()
        ]
        
        for stock in filtered_stocks:
            stock['provider'] = 'MStock'
        
        return filtered_stocks[:10]
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status (basic implementation)"""
        try:
            now = datetime.now()
            
            market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
            
            is_open = (
                now.weekday() < 5 and
                market_open_time <= now <= market_close_time
            )
            
            return {
                'market_status': 'OPEN' if is_open else 'CLOSED',
                'timestamp': now,
                'next_open': market_open_time + timedelta(days=1) if not is_open else None,
                'next_close': market_close_time if is_open else None,
                'provider': 'MStock'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return {}
    
    def get_available_symbols(self, exchange: str = 'NSE') -> List[str]:
        """Get list of available symbols from Script Master"""
        try:
            # Only try to load Script Master if we don't have it and not already loading
            if not self._instrument_tokens and not self._script_master_loading:
                if not self._ensure_script_master_loaded():
                    self.logger.info("Script Master not available, using fallback symbols")
                    return self._get_fallback_symbols()
            
            # If Script Master is available, use it
            if self._script_master_cache:
                # Extract symbols for the specified exchange
                symbols = []
                for symbol_key, instrument_data in self._script_master_cache.items():
                    if instrument_data['exchange'] == exchange.upper():
                        symbols.append(instrument_data['symbol'])
                
                # Remove duplicates and sort
                unique_symbols = sorted(list(set(symbols)))
                
                self.logger.info(f"Found {len(unique_symbols)} symbols for exchange {exchange}")
                return unique_symbols
            else:
                # Fallback if Script Master cache is empty
                return self._get_fallback_symbols()
            
        except Exception as e:
            self.logger.error(f"Error getting available symbols: {e}")
            return self._get_fallback_symbols()
    
    def _get_fallback_symbols(self) -> List[str]:
        """Fallback symbols list when Script Master is not available"""
        return [
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR',
            'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'ASIANPAINT',
            'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND',
            'BAJFINANCE', 'M&M', 'TECHM', 'HCLTECH', 'WIPRO', 'NTPC',
            'ONGC', 'POWERGRID', 'TATASTEEL', 'JSWSTEEL', 'COALINDIA',
            'DRREDDY', 'CIPLA', 'BAJAJFINSV', 'HEROMOTOCO', 'EICHERMOT',
            'BRITANNIA', 'DABUR', 'GODREJCP', 'MARICO', 'COLPAL',
            'APOLLOHOSP', 'FORTIS', 'MAXHEALTH', 'HDFCLIFE', 'SBILIFE'
        ]
    
    def test_connection(self) -> bool:
        """Test connection with MStock API"""
        try:
            if not self._ensure_authenticated():
                return False
            
            headers = self._get_headers('GET')
            response = requests.get(
                f"{self.base_url}/user/fundsummary",
                headers=headers,
                timeout=30
            )
            
            return response.status_code == 200 and response.json().get('status') == 'success'
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            'name': 'MStock',
            'broker': 'Mirae Asset',
            'type': 'Real Broker API with Script Master',
            'supports_realtime': True,
            'supports_historical': True,
            'supports_search': True,
            'authenticated': self.status == DataProviderStatus.ACTIVE,
            'rate_limits': f'Max {self.daily_request_limit} requests/day with endpoint-specific limits',
            'api_version': 'v1',
            'base_url': self.base_url,
            'script_master_loaded': len(self._instrument_tokens) > 0,
            'cached_instruments': len(self._instrument_tokens)
        }