"""
Base Data Provider Interface
Abstract base class for all data providers (Fyers, Shoonya, etc.)
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
    """Abstract base class for all data providers"""
    
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
        
        self.logger.info(f"Initialized {name} data provider")
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with the data provider"""
        pass
    
    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get basic stock information"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """Get historical price data"""
        pass
    
    @abstractmethod
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time price data for multiple symbols"""
        pass
    
    @abstractmethod
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks by name or symbol"""
        pass
    
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
            'last_request_time': self.last_request_time
        }
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for this provider (override if needed)"""
        return symbol.upper()
    
    def normalize_data_format(self, raw_data: Any) -> pd.DataFrame:
        """Convert provider-specific data format to standard format"""
        # This should be overridden by each provider
        # Standard format columns: date, open, high, low, close, volume
        pass
    
    def __str__(self):
        return f"{self.name}Provider({self.status.value})"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')"

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