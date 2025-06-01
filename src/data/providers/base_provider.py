"""
Enhanced Base Data Provider Interface with Symbol Normalization
Extends your existing base_provider.py with symbol standardization
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import pandas as pd
import logging
from enum import Enum

class DataProviderStatus(Enum):
    """Data provider status"""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    INACTIVE = "inactive"

class DataProviderPriority(Enum):
    """Data provider priority levels"""
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3
    BACKUP = 4

class BaseDataProvider(ABC):
    """Enhanced abstract base class for all data providers with symbol normalization"""
    
    def __init__(self, name: str, priority: DataProviderPriority = DataProviderPriority.SECONDARY):
        self.name = name
        self.priority = priority
        self.status = DataProviderStatus.INACTIVE
        self.logger = logging.getLogger(f"providers.{name}")
        self.rate_limit_reset_time = None
        self.error_count = 0
        self.max_errors = 5
        self.last_request_time = None
        
        # Provider specific settings
        self.rate_limit_delay = 1.0  # Default delay between requests
        self.daily_request_limit = 1000  # Default daily limit
        self.requests_today = 0
        
        # Symbol normalization cache
        self._symbol_cache = {}
        self._reverse_cache = {}
        
        self.logger.info(f"Initialized {name} data provider with symbol normalization")
    
    # ============================================================================
    # SYMBOL NORMALIZATION METHODS (NEW)
    # ============================================================================
    
    def normalize_symbol(self, symbol: str, exchange: str = 'NSE') -> str:
        """
        Convert clean symbol to provider-specific format
        
        Args:
            symbol: Clean symbol (e.g., "RELIANCE")
            exchange: Exchange name (default: NSE)
            
        Returns:
            Provider-specific symbol format
            
        Example:
            Fyers: "RELIANCE" → "NSE:RELIANCE-EQ"
            Shoonya: "RELIANCE" → "RELIANCE"  
            MStock: "RELIANCE" → "2885" (token)
        """
        # Cache key for performance
        cache_key = f"{symbol}_{exchange}"
        
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        # Get provider-specific format
        normalized = self._provider_normalize_symbol(symbol, exchange)
        
        # Cache for future use
        self._symbol_cache[cache_key] = normalized
        self._reverse_cache[normalized] = symbol
        
        return normalized
    
    def denormalize_symbol(self, provider_symbol: str) -> str:
        """
        Convert provider-specific symbol back to clean format
        
        Args:
            provider_symbol: Provider-specific symbol
            
        Returns:
            Clean symbol format
            
        Example:
            Fyers: "NSE:RELIANCE-EQ" → "RELIANCE"
            Shoonya: "RELIANCE" → "RELIANCE"
        """
        # Check reverse cache first
        if provider_symbol in self._reverse_cache:
            return self._reverse_cache[provider_symbol]
        
        # Get clean format
        clean_symbol = self._provider_denormalize_symbol(provider_symbol)
        
        # Cache for future use
        self._reverse_cache[provider_symbol] = clean_symbol
        self._symbol_cache[f"{clean_symbol}_NSE"] = provider_symbol
        
        return clean_symbol
    
    def _provider_normalize_symbol(self, symbol: str, exchange: str = 'NSE') -> str:
        """
        Provider-specific symbol normalization - OVERRIDE in each provider
        
        Default implementation: no change
        """
        return symbol
    
    def _provider_denormalize_symbol(self, provider_symbol: str) -> str:
        """
        Provider-specific symbol denormalization - OVERRIDE in each provider
        
        Default implementation: no change  
        """
        return provider_symbol
    
    def get_symbol_mappings(self) -> Dict[str, str]:
        """Get current symbol mappings (for debugging)"""
        return self._symbol_cache.copy()
    
    def clear_symbol_cache(self):
        """Clear symbol normalization cache"""
        self._symbol_cache.clear()
        self._reverse_cache.clear()
        self.logger.debug("Symbol cache cleared")
    
    # ============================================================================
    # ENHANCED API METHODS WITH AUTOMATIC SYMBOL NORMALIZATION
    # ============================================================================
    
    def get_stock_info_normalized(self, symbol: str, exchange: str = 'NSE') -> Optional[Dict[str, Any]]:
        """
        Get stock info with automatic symbol normalization
        
        Args:
            symbol: Clean symbol (e.g., "RELIANCE")
            exchange: Exchange name
            
        Returns:
            Stock info dict with clean symbol in result
        """
        try:
            # Convert to provider format
            provider_symbol = self.normalize_symbol(symbol, exchange)
            
            # Get data using provider format
            result = self.get_stock_info(provider_symbol)
            
            if result:
                # Ensure result contains clean symbol
                result['symbol'] = symbol
                result['provider_symbol'] = provider_symbol
                result['exchange'] = exchange
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting normalized stock info for {symbol}: {e}")
            return None
    
    def get_historical_data_normalized(self, symbol: str, start_date: date, end_date: date, 
                                     interval: str = "1D", exchange: str = 'NSE') -> Optional[pd.DataFrame]:
        """
        Get historical data with automatic symbol normalization
        
        Args:
            symbol: Clean symbol (e.g., "RELIANCE")
            start_date: Start date
            end_date: End date
            interval: Data interval
            exchange: Exchange name
            
        Returns:
            DataFrame with clean symbol in 'symbol' column
        """
        try:
            # Convert to provider format
            provider_symbol = self.normalize_symbol(symbol, exchange)
            
            # Get data using provider format
            data = self.get_historical_data(provider_symbol, start_date, end_date, interval)
            
            if data is not None and not data.empty:
                # Ensure DataFrame contains clean symbol
                data = data.copy()
                data['symbol'] = symbol
                data['provider_symbol'] = provider_symbol
                data['exchange'] = exchange
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting normalized historical data for {symbol}: {e}")
            return None
    
    def get_real_time_data_normalized(self, symbols: List[str], exchange: str = 'NSE') -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get real-time data with automatic symbol normalization
        
        Args:
            symbols: List of clean symbols
            exchange: Exchange name
            
        Returns:
            Dict with clean symbols as keys
        """
        try:
            # Convert all symbols to provider format
            provider_symbols = [self.normalize_symbol(symbol, exchange) for symbol in symbols]
            
            # Get data using provider format
            provider_data = self.get_real_time_data(provider_symbols)
            
            if not provider_data:
                return None
            
            # Convert back to clean symbols
            normalized_data = {}
            for i, clean_symbol in enumerate(symbols):
                if i < len(provider_symbols):
                    provider_symbol = provider_symbols[i]
                    if provider_symbol in provider_data:
                        data = provider_data[provider_symbol].copy()
                        data['symbol'] = clean_symbol
                        data['provider_symbol'] = provider_symbol
                        data['exchange'] = exchange
                        normalized_data[clean_symbol] = data
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Error getting normalized real-time data: {e}")
            return None
    
    # ============================================================================
    # ORIGINAL ABSTRACT METHODS (YOUR EXISTING INTERFACE)
    # ============================================================================
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with the data provider"""
        pass
    
    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get basic stock information (uses provider-specific symbol format)"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """Get historical price data (uses provider-specific symbol format)"""
        pass
    
    @abstractmethod
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time price data for multiple symbols (uses provider-specific symbol format)"""
        pass
    
    @abstractmethod
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks by name or symbol"""
        pass
    
    # ============================================================================
    # YOUR EXISTING METHODS (UNCHANGED)
    # ============================================================================
    
    def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = datetime.now()
        
        # Check if we've exceeded daily limits
        if self.requests_today >= self.daily_request_limit:
            self.status = DataProviderStatus.RATE_LIMITED
            self.logger.warning(f"{self.name}: Daily request limit reached")
            return False
        
        # Check if we need to wait between requests
        if (self.last_request_time and 
            (current_time - self.last_request_time).total_seconds() < self.rate_limit_delay):
            return False
        
        return True
    
    def record_request(self):
        """Record that a request was made"""
        self.last_request_time = datetime.now()
        self.requests_today += 1
    
    def record_error(self, error: Exception):
        """Record an error and update status if needed"""
        self.error_count += 1
        self.logger.error(f"{self.name}: Error occurred - {error}")
        
        if self.error_count >= self.max_errors:
            self.status = DataProviderStatus.ERROR
            self.logger.error(f"{self.name}: Too many errors, marking as ERROR status")
    
    def reset_error_count(self):
        """Reset error count on successful request"""
        if self.error_count > 0:
            self.error_count = 0
            if self.status == DataProviderStatus.ERROR:
                self.status = DataProviderStatus.ACTIVE
                self.logger.info(f"{self.name}: Errors cleared, back to ACTIVE status")
    
    def is_available(self) -> bool:
        """Check if provider is available for use"""
        return self.status in [DataProviderStatus.ACTIVE, DataProviderStatus.INACTIVE] and self.check_rate_limit()
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information"""
        return {
            'name': self.name,
            'status': self.status.value,
            'priority': self.priority.value,
            'error_count': self.error_count,
            'requests_today': self.requests_today,
            'daily_limit': self.daily_request_limit,
            'is_available': self.is_available(),
            'last_request_time': self.last_request_time,
            'symbol_cache_size': len(self._symbol_cache)
        }
    
    def __str__(self):
        return f"{self.name}Provider({self.status.value})"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')"

# ============================================================================
# ENHANCED EXCEPTION CLASSES
# ============================================================================

class DataProviderError(Exception):
    """Custom exception for data provider errors"""
    
    def __init__(self, provider_name: str, message: str, error_type: str = "general"):
        self.provider_name = provider_name
        self.error_type = error_type
        super().__init__(f"{provider_name}: {message}")

class RateLimitError(DataProviderError):
    """Exception for rate limit errors"""
    
    def __init__(self, provider_name: str, reset_time: Optional[datetime] = None):
        self.reset_time = reset_time
        message = f"Rate limit exceeded"
        if reset_time:
            message += f", resets at {reset_time}"
        super().__init__(provider_name, message, "rate_limit")

class AuthenticationError(DataProviderError):
    """Exception for authentication errors"""
    
    def __init__(self, provider_name: str, message: str = "Authentication failed"):
        super().__init__(provider_name, message, "authentication")

class DataNotFoundError(DataProviderError):
    """Exception when requested data is not found"""
    
    def __init__(self, provider_name: str, symbol: str, message: str = None):
        self.symbol = symbol
        message = message or f"Data not found for {symbol}"
        super().__init__(provider_name, message, "data_not_found")

class SymbolNormalizationError(DataProviderError):
    """Exception for symbol normalization errors"""
    
    def __init__(self, provider_name: str, symbol: str, message: str = None):
        self.symbol = symbol
        message = message or f"Failed to normalize symbol {symbol}"
        super().__init__(provider_name, message, "symbol_normalization")

# Example usage
if __name__ == "__main__":
    print("✅ Enhanced Base Data Provider with Symbol Normalization")
    print("🔧 Key Features Added:")
    print("   • normalize_symbol() - Convert clean symbols to provider format")
    print("   • denormalize_symbol() - Convert provider symbols back to clean format")
    print("   • get_*_normalized() methods - Automatic symbol handling")
    print("   • Symbol caching for performance")
    print("   • Backward compatibility with existing interface")