"""
Shoonya Data Provider

Provides market data from Shoonya (Finvasia) broker API.
Extends BaseDataProvider to integrate with the multi-provider system.
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

from .base_provider import BaseDataProvider
from ..auth.shoonya_auth import ShoonyaAuthenticator

logger = logging.getLogger(__name__)

class ShoonyaProvider(BaseDataProvider):
    """
    Shoonya API Data Provider
    
    Fetches real-time quotes, historical data, and market information
    from Shoonya (Finvasia) broker API.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Shoonya provider
        
        Args:
            config: Configuration dictionary (optional)
        """
        super().__init__("Shoonya", config or {})
        self.authenticator = None
        self.api_instance = None
        self._initialize_provider()
    
    def _initialize_provider(self) -> bool:
        """
        Initialize the Shoonya provider and authenticate
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Create authenticator
            self.authenticator = ShoonyaAuthenticator()
            
            if not self.authenticator.validate_credentials():
                logger.error("Invalid Shoonya credentials")
                return False
            
            # Get authenticated session
            token = self.authenticator.get_access_token()
            if token:
                self.api_instance = self.authenticator.get_authenticated_session()
                if self.api_instance:
                    logger.info("✅ Shoonya provider initialized successfully")
                    return True
            
            logger.error("❌ Failed to get authenticated Shoonya session")
            return False
            
        except Exception as e:
            logger.error(f"❌ Shoonya provider initialization failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if Shoonya provider is available and authenticated
        
        Returns:
            bool: True if provider is ready to use
        """
        try:
            if not self.authenticator or not self.api_instance:
                return False
            
            return self.authenticator.is_authenticated()
            
        except Exception as e:
            logger.error(f"Shoonya availability check failed: {e}")
            return False
    
    def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a symbol
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")
            exchange: Exchange name (NSE, BSE)
            
        Returns:
            Dict containing quote data or None if failed
        """
        try:
            if not self.is_available():
                logger.error("Shoonya provider not available")
                return None
            
            # First, search for the symbol to get token
            token = self._get_symbol_token(symbol, exchange)
            if not token:
                logger.error(f"Could not find token for {symbol} on {exchange}")
                return None
            
            # Get quote using token
            response = self.api_instance.get_quotes(exchange, token)
            
            if response and response.get('stat') == 'Ok':
                quote_data = self._parse_quote_response(response, symbol)
                if quote_data:
                    logger.info(f"✅ Retrieved quote for {symbol}: ₹{quote_data.get('ltp', 'N/A')}")
                return quote_data
            else:
                error_msg = response.get('emsg', 'Unknown error') if response else 'No response'
                logger.error(f"❌ Quote request failed for {symbol}: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting quote for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = 30, exchange: str = "NSE") -> Optional[pd.DataFrame]:
        """
        Get historical data for a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
            exchange: Exchange name
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            if not self.is_available():
                logger.error("Shoonya provider not available")
                return None
            
            # Get symbol token
            token = self._get_symbol_token(symbol, exchange)
            if not token:
                logger.error(f"Could not find token for {symbol} on {exchange}")
                return None
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Convert to unix timestamps (Shoonya expects seconds since epoch)
            start_timestamp = str(int(start_date.timestamp()))
            end_timestamp = str(int(end_date.timestamp()))
            
            # Get historical data
            response = self.api_instance.get_time_price_series(
                exchange=exchange,
                token=token,
                starttime=start_timestamp,
                endtime=end_timestamp
            )
            
            if response and response.get('stat') == 'Ok':
                df = self._parse_historical_response(response, symbol)
                if df is not None and not df.empty:
                    logger.info(f"✅ Retrieved {len(df)} days of historical data for {symbol}")
                    return df
                else:
                    logger.warning(f"⚠️ No historical data available for {symbol}")
                    return None
            else:
                error_msg = response.get('emsg', 'Unknown error') if response else 'No response'
                logger.error(f"❌ Historical data request failed for {symbol}: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting historical data for {symbol}: {e}")
            return None
    
    def _get_symbol_token(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get the token for a symbol by searching
        
        Args:
            symbol: Stock symbol
            exchange: Exchange name
            
        Returns:
            Token string or None if not found
        """
        try:
            # Search for the symbol
            response = self.api_instance.searchscrip(exchange=exchange, searchtext=symbol)
            
            if response and response.get('stat') == 'Ok' and 'values' in response:
                # Look for exact match first
                for item in response['values']:
                    tsym = item.get('tsym', '')
                    # For equity stocks, look for symbol-EQ pattern
                    if tsym == f"{symbol}-EQ" or tsym == symbol:
                        token = item.get('token')
                        logger.debug(f"✅ Found token {token} for {symbol} ({tsym})")
                        return token
                
                # If no exact match, take the first result
                if response['values']:
                    first_result = response['values'][0]
                    token = first_result.get('token')
                    tsym = first_result.get('tsym', '')
                    logger.warning(f"⚠️ Using partial match: {token} for {symbol} (found {tsym})")
                    return token
            
            logger.error(f"❌ No token found for {symbol} on {exchange}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for token for {symbol}: {e}")
            return None
    
    def _parse_quote_response(self, response: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Parse quote response from Shoonya API
        
        Args:
            response: Raw API response
            symbol: Stock symbol for reference
            
        Returns:
            Standardized quote dictionary
        """
        try:
            # Shoonya quote response structure
            ltp = float(response.get('lp', 0)) if response.get('lp') else 0
            open_price = float(response.get('o', 0)) if response.get('o') else 0
            high_price = float(response.get('h', 0)) if response.get('h') else 0
            low_price = float(response.get('l', 0)) if response.get('l') else 0
            close_price = float(response.get('c', 0)) if response.get('c') else 0  # Previous close
            volume = int(response.get('v', 0)) if response.get('v') else 0
            
            # Calculate change and change percentage
            if close_price > 0:
                change = ltp - close_price
                change_pct = (change / close_price) * 100
            else:
                change = 0
                change_pct = 0
            
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
            logger.error(f"Error parsing quote response: {e}")
            return None
    
    def _parse_historical_response(self, response: Dict, symbol: str) -> Optional[pd.DataFrame]:
        """
        Parse historical data response from Shoonya API
        
        Args:
            response: Raw API response
            symbol: Stock symbol for reference
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            if 'values' not in response or not response['values']:
                logger.warning(f"No historical data in response for {symbol}")
                return None
            
            data = []
            for item in response['values']:
                try:
                    # Parse Shoonya historical data format
                    date_str = item.get('time', '')
                    date_obj = datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S') if date_str else datetime.now()
                    
                    data.append({
                        'date': date_obj,
                        'open': float(item.get('into', 0)),
                        'high': float(item.get('inth', 0)),
                        'low': float(item.get('intl', 0)),
                        'close': float(item.get('intc', 0)),
                        'volume': int(item.get('intv', 0))
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid data point: {e}")
                    continue
            
            if not data:
                logger.warning(f"No valid historical data points for {symbol}")
                return None
            
            df = pd.DataFrame(data)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # Add symbol column
            df['symbol'] = symbol
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing historical response: {e}")
            return None
    
    def get_multiple_quotes(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get quotes for multiple symbols
        
        Args:
            symbols: List of stock symbols
            exchange: Exchange name
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        quotes = {}
        
        for symbol in symbols:
            try:
                quote = self.get_quote(symbol, exchange)
                quotes[symbol] = quote
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error getting quote for {symbol}: {e}")
                quotes[symbol] = None
        
        return quotes
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider
        
        Returns:
            Dictionary with provider information
        """
        return {
            'name': 'Shoonya',
            'broker': 'Finvasia',
            'type': 'Real Broker API',
            'supports_realtime': True,
            'supports_historical': True,
            'exchanges': ['NSE', 'BSE', 'NFO', 'CDS'],
            'authenticated': self.is_available(),
            'rate_limits': 'Standard broker API limits apply'
        }