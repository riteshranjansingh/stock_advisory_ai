"""
Optimized Shoonya Data Provider - Based on Official API Documentation

Provides market data from Shoonya (Finvasia) broker API.
Optimized using official Shoonya API documentation patterns.
"""

import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import time
import calendar

from .base_provider import BaseDataProvider, DataProviderPriority, DataProviderStatus
from src.auth.shoonya_auth import ShoonyaAuthenticator

logger = logging.getLogger(__name__)

class ShoonyaProvider(BaseDataProvider):
    """
    Optimized Shoonya API Data Provider
    
    Uses official Shoonya API patterns for maximum efficiency and reliability.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Shoonya provider with optimizations"""
        super().__init__("Shoonya", DataProviderPriority.PRIMARY)
        self.config = config or {}
        self.authenticator = None
        self.api_instance = None
        
        # Caching for performance
        self._token_cache = {}  # Cache symbol->token mappings
        self._security_info_cache = {}  # Cache detailed security info
        
        # Rate limiting settings (from official docs)
        self.rate_limit_delay = 0.5  # 500ms between requests 
        self.daily_request_limit = 3000
        
        # Auto-authenticate during initialization
        self._initialize_provider()
        
        logger.info("Optimized Shoonya provider initialized")
    
    def _initialize_provider(self) -> bool:
        """Initialize with authentication"""
        try:
            self.authenticator = ShoonyaAuthenticator()
            
            if not self.authenticator.validate_credentials():
                logger.warning("Shoonya credentials not available")
                return False
            
            token = self.authenticator.get_access_token()
            if token:
                self.api_instance = self.authenticator.get_authenticated_session()
                if self.api_instance:
                    self.status = DataProviderStatus.ACTIVE
                    logger.info("✅ Optimized Shoonya provider authenticated")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Shoonya initialization failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        try:
            if not self.authenticator or not self.api_instance:
                return False
            return self.authenticator.is_authenticated()
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            return False
    
    def authenticate(self, credentials: Dict[str, str] = None) -> bool:
        """Authenticate with Shoonya API"""
        try:
            if not self.authenticator:
                self.authenticator = ShoonyaAuthenticator()
            
            if not self.authenticator.validate_credentials():
                return False
            
            token = self.authenticator.get_access_token()
            if token:
                self.api_instance = self.authenticator.get_authenticated_session()
                if self.api_instance:
                    self.status = DataProviderStatus.ACTIVE
                    return True
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive stock information using get_security_info"""
        try:
            if not self.is_available():
                return None
            
            # Check cache first
            cache_key = f"{symbol}_NSE"
            if cache_key in self._security_info_cache:
                return self._security_info_cache[cache_key]
            
            # Get token for the symbol
            token = self._get_symbol_token_cached(symbol, "NSE")
            if not token:
                return None
            
            # Use get_security_info for comprehensive data (from official docs)
            response = self.api_instance.get_security_info(exchange="NSE", token=token)
            
            if response and response.get('stat') == 'Ok':
                stock_info = {
                    'symbol': symbol.upper(),
                    'name': response.get('cname', symbol),
                    'trading_symbol': response.get('tsym', f"{symbol}-EQ"),
                    'exchange': response.get('exch', 'NSE'),
                    'segment': response.get('seg', 'EQT'),
                    'instrument_type': response.get('instname', 'EQ'),
                    'isin': response.get('isin', ''),
                    'lot_size': int(response.get('ls', 1)),
                    'tick_size': float(response.get('ti', 0.05)),
                    'price_precision': int(response.get('pp', 2)),
                    'multiplier': int(response.get('mult', 1)),
                    'token': token,
                    'freeze_qty': response.get('frzqty'),
                    'var_margin': response.get('varmrg')
                }
                
                # Cache the result
                self._security_info_cache[cache_key] = stock_info
                logger.info(f"✅ Retrieved comprehensive info for {symbol}")
                return stock_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: date = None, end_date: date = None, 
                          interval: str = "1D", days: int = None) -> Optional[pd.DataFrame]:
        """
        Optimized historical data retrieval using proper Shoonya API methods
        """
        try:
            if not self.is_available():
                return None
            
            # Handle date parameters
            if days is not None:
                end_date = date.today()
                start_date = end_date - timedelta(days=days)
            elif start_date is None or end_date is None:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
            
            logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            # Method 1: Try get_daily_price_series (official daily data API)
            try:
                trading_symbol = f"{symbol}-EQ"
                
                # Convert dates to epoch timestamps (as per official docs)
                # API expects string timestamps, not formatted dates!
                start_timestamp = str(int(datetime.combine(start_date, datetime.min.time()).timestamp()))
                end_timestamp = str(int(datetime.combine(end_date, datetime.min.time()).timestamp()))
                
                logger.debug(f"Calling daily API for {symbol}: start={start_timestamp}, end={end_timestamp}")
                
                response = self.api_instance.get_daily_price_series(
                    exchange="NSE",
                    tradingsymbol=trading_symbol,
                    startdate=start_timestamp,
                    enddate=end_timestamp
                )
                
                logger.debug(f"Daily API response type: {type(response)}, length: {len(response) if response else 0}")
                
                if response and isinstance(response, list) and len(response) > 0:
                    df = self._parse_daily_price_series(response, symbol)
                    if df is not None and not df.empty:
                        logger.info(f"✅ Retrieved {len(df)} days of data using daily API for {symbol}")
                        return df
                else:
                    logger.debug(f"Daily API returned empty/invalid response for {symbol}")
                        
            except Exception as e:
                logger.debug(f"Daily API failed for {symbol}: {e}")
                
            # Method 2: Fallback to get_time_price_series with daily interval
            logger.info(f"Falling back to time series API for {symbol}")
            try:
                token = self._get_symbol_token_cached(symbol, "NSE")
                if not token:
                    logger.error(f"Could not get token for {symbol}")
                    return None
                
                start_timestamp = str(int(datetime.combine(start_date, datetime.min.time()).timestamp()))
                end_timestamp = str(int(datetime.combine(end_date, datetime.min.time()).timestamp()))
                
                logger.debug(f"Calling time series API for {symbol}: token={token}")
                
                # Use daily interval (1440 minutes = 1 day) as per docs
                response = self.api_instance.get_time_price_series(
                    exchange="NSE",
                    token=token,
                    starttime=start_timestamp,
                    endtime=end_timestamp,
                    interval=1440  # Daily interval
                )
                
                logger.debug(f"Time series API response type: {type(response)}, length: {len(response) if response else 0}")
                
                if response and isinstance(response, list) and len(response) > 0:
                    df = self._parse_time_price_series(response, symbol)
                    if df is not None and not df.empty:
                        logger.info(f"✅ Retrieved {len(df)} records using time series API for {symbol}")
                        return df
                else:
                    logger.warning(f"Time series API returned empty response for {symbol}")
                        
            except Exception as e:
                logger.error(f"Time series API failed for {symbol}: {e}")
            
            logger.error(f"Both daily and time series APIs failed for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Historical data error for {symbol}: {e}")
            return None
    
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time data efficiently"""
        try:
            if not self.is_available():
                return None
            
            result = {}
            for symbol in symbols:
                quote = self.get_quote(symbol)
                if quote:
                    result[symbol] = quote
                time.sleep(self.rate_limit_delay)  # Respect rate limits
            
            logger.info(f"✅ Retrieved real-time data for {len(result)}/{len(symbols)} symbols")
            return result if result else None
            
        except Exception as e:
            logger.error(f"Real-time data error: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Optimized stock search using searchscrip API"""
        try:
            if not self.is_available():
                return []
            
            response = self.api_instance.searchscrip(exchange="NSE", searchtext=query)
            
            results = []
            if response and response.get('stat') == 'Ok' and 'values' in response:
                for item in response['values']:
                    try:
                        # Extract and standardize data as per official API docs
                        tsym = item.get('tsym', '')
                        
                        # Focus on equity instruments
                        if not tsym.endswith('-EQ'):
                            continue
                            
                        symbol_clean = tsym.replace('-EQ', '')
                        
                        symbol_info = {
                            'symbol': symbol_clean,
                            'name': symbol_clean,  # Search doesn't provide company name
                            'trading_symbol': tsym,
                            'exchange': item.get('exch', 'NSE'),
                            'token': item.get('token', ''),
                            'lot_size': int(item.get('ls', 1)),
                            'tick_size': float(item.get('ti', 0.05)),
                            'price_precision': int(item.get('pp', 2))
                        }
                        
                        results.append(symbol_info)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing search result: {e}")
                        continue
            
            logger.info(f"Found {len(results)} equity results for query '{query}'")
            return results[:20]  # Limit results
            
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")
            return []
    
    def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        """Optimized quote retrieval"""
        try:
            if not self.is_available():
                return None
            
            token = self._get_symbol_token_cached(symbol, exchange)
            if not token:
                return None
            
            response = self.api_instance.get_quotes(exchange=exchange, token=token)
            
            if response and response.get('stat') == 'Ok':
                quote_data = self._parse_quote_response(response, symbol)
                if quote_data:
                    logger.debug(f"✅ Quote for {symbol}: ₹{quote_data.get('ltp', 'N/A')}")
                return quote_data
            else:
                error_msg = response.get('emsg', 'Unknown error') if response else 'No response'
                logger.warning(f"Quote failed for {symbol}: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Quote error for {symbol}: {e}")
            return None
    
    def get_multiple_quotes(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple quotes with rate limiting"""
        quotes = {}
        for symbol in symbols:
            quotes[symbol] = self.get_quote(symbol, exchange)
            time.sleep(self.rate_limit_delay)
        return quotes
    
    def _get_symbol_token_cached(self, symbol: str, exchange: str = "NSE") -> Optional[str]:
        """Get token with caching for performance"""
        cache_key = f"{symbol}_{exchange}"
        
        # Check cache first
        if cache_key in self._token_cache:
            return self._token_cache[cache_key]
        
        try:
            response = self.api_instance.searchscrip(exchange=exchange, searchtext=symbol)
            
            if response and response.get('stat') == 'Ok' and 'values' in response:
                # Look for exact match
                for item in response['values']:
                    tsym = item.get('tsym', '')
                    if tsym == f"{symbol}-EQ" or tsym == symbol:
                        token = item.get('token')
                        if token:
                            self._token_cache[cache_key] = token  # Cache it
                            return token
                
                # Fallback to first result
                if response['values']:
                    token = response['values'][0].get('token')
                    if token:
                        self._token_cache[cache_key] = token
                        return token
            
            return None
            
        except Exception as e:
            logger.error(f"Token search error for {symbol}: {e}")
            return None
    
    def _parse_quote_response(self, response: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """Parse quote response using official field names"""
        try:
            # Official Shoonya quote field names from docs
            ltp = float(response.get('lp', 0)) if response.get('lp') else 0
            open_price = float(response.get('o', 0)) if response.get('o') else 0
            high_price = float(response.get('h', 0)) if response.get('h') else 0
            low_price = float(response.get('l', 0)) if response.get('l') else 0
            close_price = float(response.get('c', 0)) if response.get('c') else 0
            volume = int(response.get('v', 0)) if response.get('v') else 0
            
            # Calculate change
            change = ltp - close_price if close_price > 0 else 0
            change_pct = (change / close_price * 100) if close_price > 0 else 0
            
            return {
                'symbol': symbol,
                'ltp': ltp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'change': change,
                'change_pct': change_pct,
                'provider': 'Shoonya',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Quote parsing error: {e}")
            return None
    
    def _parse_daily_price_series(self, response: List, symbol: str) -> Optional[pd.DataFrame]:
        """Parse daily price series response - handles JSON strings format with correct date parsing"""
        try:
            import json
            
            data = []
            for item in response:
                try:
                    # Shoonya daily API returns JSON strings, not objects!
                    if isinstance(item, str):
                        # Parse the JSON string first
                        item_dict = json.loads(item)
                    else:
                        # In case it's already a dict
                        item_dict = item
                    
                    # Parse date - CORRECT FORMAT from official docs is %d-%b-%Y
                    time_str = item_dict.get('time', '')
                    if time_str:
                        try:
                            # Official Shoonya format: "27-MAY-2025" = %d-%b-%Y
                            date_obj = datetime.strptime(time_str, '%d-%b-%Y')
                        except ValueError:
                            try:
                                # Fallback formats
                                date_obj = datetime.strptime(time_str, '%d-%m-%Y')
                            except ValueError:
                                try:
                                    date_obj = datetime.strptime(time_str, '%d-%m-%Y %H:%M:%S')
                                except ValueError:
                                    logger.warning(f"Cannot parse date format: {time_str}")
                                    continue
                    else:
                        continue
                    
                    # Map daily data fields (from official docs)
                    data.append({
                        'date': date_obj,
                        'open': float(item_dict.get('into', item_dict.get('o', 0))),
                        'high': float(item_dict.get('inth', item_dict.get('h', 0))),
                        'low': float(item_dict.get('intl', item_dict.get('l', 0))),
                        'close': float(item_dict.get('intc', item_dict.get('c', 0))),
                        'volume': int(float(item_dict.get('intv', item_dict.get('v', 0))))  # Convert to int via float first
                    })
                    
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid daily data point for {symbol}: {e}")
                    continue
            
            if not data:
                logger.warning(f"No valid daily data points parsed for {symbol}")
                return None
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            df['symbol'] = symbol
            
            # Clean data - remove invalid entries
            df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
            
            logger.info(f"✅ Successfully parsed {len(df)} daily records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Daily data parsing error for {symbol}: {e}")
            return None
    
    def _parse_time_price_series(self, response: List, symbol: str) -> Optional[pd.DataFrame]:
        """Parse time price series response - handles both dict and JSON string formats"""
        try:
            import json
            
            data = []
            for item in response:
                try:
                    # Handle both JSON string and dict formats
                    if isinstance(item, str):
                        try:
                            item_dict = json.loads(item)
                        except json.JSONDecodeError:
                            logger.warning(f"Cannot parse JSON string: {item}")
                            continue
                    else:
                        item_dict = item
                    
                    # Parse time with correct Shoonya date formats
                    time_str = item_dict.get('time', '')
                    if time_str:
                        try:
                            # Primary format from Shoonya: "27-MAY-2025" or "21-SEP-2022"  
                            date_obj = datetime.strptime(time_str, '%d-%b-%Y')
                        except ValueError:
                            try:
                                # Format with time: "27-MAY-2025 15:30:00"
                                date_obj = datetime.strptime(time_str, '%d-%b-%Y %H:%M:%S')
                            except ValueError:
                                try:
                                    # Numeric format: "27-05-2025"
                                    date_obj = datetime.strptime(time_str, '%d-%m-%Y')
                                except ValueError:
                                    try:
                                        # Numeric with time: "27-05-2025 15:30:00"
                                        date_obj = datetime.strptime(time_str, '%d-%m-%Y %H:%M:%S')
                                    except ValueError:
                                        logger.debug(f"Cannot parse time format: {time_str}")
                                        continue
                    else:
                        continue
                    
                    data.append({
                        'date': date_obj,
                        'open': float(item_dict.get('into', 0)),    # into = interval open
                        'high': float(item_dict.get('inth', 0)),    # inth = interval high
                        'low': float(item_dict.get('intl', 0)),     # intl = interval low
                        'close': float(item_dict.get('intc', 0)),   # intc = interval close
                        'volume': int(float(item_dict.get('intv', 0)))     # intv = interval volume
                    })
                    
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.debug(f"Skipping time series data point for {symbol}: {e}")
                    continue
            
            if not data:
                logger.warning(f"No valid time series data points for {symbol}")
                return None
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            df['symbol'] = symbol
            
            # Clean invalid data
            df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
            
            # If we got intraday data, aggregate to daily
            if len(df) > 50:
                logger.info(f"Got {len(df)} intraday records, aggregating to daily for {symbol}")
                df = self._aggregate_to_daily(df, symbol)
            
            logger.info(f"✅ Successfully parsed {len(df)} time series records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Time series parsing error for {symbol}: {e}")
            return None
    
    def _aggregate_to_daily(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Aggregate intraday data to daily OHLCV"""
        try:
            df['date_only'] = df['date'].dt.date
            
            daily_data = df.groupby('date_only').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).reset_index()
            
            daily_data['date'] = pd.to_datetime(daily_data['date_only'])
            daily_data = daily_data.drop('date_only', axis=1)
            daily_data['symbol'] = symbol
            
            daily_data = daily_data.sort_values('date').reset_index(drop=True)
            
            logger.info(f"✅ Aggregated to {len(daily_data)} daily records for {symbol}")
            return daily_data
            
        except Exception as e:
            logger.error(f"Aggregation error: {e}")
            return df
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Provider information"""
        return {
            'name': 'Shoonya',
            'broker': 'Finvasia',
            'type': 'Real Broker API (Optimized)',
            'supports_realtime': True,
            'supports_historical': True,
            'supports_websocket': True,  # Available but not implemented yet
            'exchanges': ['NSE', 'BSE', 'NFO', 'CDS', 'MCX'],
            'authenticated': self.is_available(),
            'rate_limits': 'Optimized with caching and delays',
            'optimizations': ['Token caching', 'Security info caching', 'Rate limiting', 'Official API patterns']
        }
    
    def test_connection(self) -> bool:
        """Test connection"""
        try:
            if not self.is_available():
                return False
            response = self.api_instance.get_limits()
            return response and response.get('stat') == 'Ok'
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False