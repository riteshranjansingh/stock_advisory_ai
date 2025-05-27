"""
Data Provider Manager
Manages multiple data providers with fallback logic and smart switching
"""

from typing import Dict, List, Optional, Any, Type
from datetime import datetime, date
import pandas as pd
import logging
import time
from .base_provider import (
    BaseDataProvider, DataProviderStatus, DataProviderPriority,
    DataProviderError, RateLimitError, AuthenticationError, DataNotFoundError
)

class DataProviderManager:
    """Manages multiple data providers with intelligent fallback"""
    
    def __init__(self):
        self.providers: Dict[str, BaseDataProvider] = {}
        self.provider_order: List[str] = []  # Ordered by priority
        self.current_provider: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        
        # Manager settings
        self.max_retries_per_provider = 3
        self.fallback_delay = 2.0  # Seconds to wait before trying next provider
        self.provider_switch_threshold = 5  # Errors before switching
        
        self.logger.info("Data Provider Manager initialized")
    
    def register_provider(self, provider: BaseDataProvider, credentials: Dict[str, str] = None) -> bool:
        """Register a new data provider"""
        try:
            # Authenticate if credentials provided
            if credentials:
                auth_success = provider.authenticate(credentials)
                if not auth_success:
                    self.logger.error(f"Failed to authenticate {provider.name}")
                    return False
                
                provider.status = DataProviderStatus.ACTIVE
            
            # Add to provider registry
            self.providers[provider.name] = provider
            
            # Update provider order based on priority
            self._update_provider_order()
            
            # Set as current provider if it's the highest priority active one
            if not self.current_provider and provider.status == DataProviderStatus.ACTIVE:
                self.current_provider = provider.name
            
            self.logger.info(f"Registered {provider.name} provider (priority: {provider.priority.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering {provider.name}: {e}")
            return False
    
    def _update_provider_order(self):
        """Update provider order based on priority and status"""
        active_providers = [
            (name, provider) for name, provider in self.providers.items()
            if provider.status in [DataProviderStatus.ACTIVE, DataProviderStatus.INACTIVE]
        ]
        
        # Sort by priority (lower number = higher priority)
        active_providers.sort(key=lambda x: x[1].priority.value)
        
        self.provider_order = [name for name, _ in active_providers]
        
        self.logger.debug(f"Provider order updated: {self.provider_order}")
    
    def get_active_provider(self) -> Optional[BaseDataProvider]:
        """Get the currently active provider"""
        if not self.current_provider or self.current_provider not in self.providers:
            self._select_best_provider()
        
        if self.current_provider:
            return self.providers[self.current_provider]
        
        return None
    
    def _select_best_provider(self) -> bool:
        """Select the best available provider"""
        self._update_provider_order()
        
        for provider_name in self.provider_order:
            provider = self.providers[provider_name]
            if provider.is_available():
                if self.current_provider != provider_name:
                    self.logger.info(f"Switching to provider: {provider_name}")
                    self.current_provider = provider_name
                return True
        
        self.logger.error("No available providers found")
        self.current_provider = None
        return False
    
    def _try_with_fallback(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute operation with fallback to other providers"""
        last_error = None
        
        # Try with each provider in order
        for attempt, provider_name in enumerate(self.provider_order):
            provider = self.providers[provider_name]
            
            if not provider.is_available():
                self.logger.debug(f"Skipping {provider_name} - not available")
                continue
            
            self.logger.debug(f"Trying {operation_name} with {provider_name}")
            
            for retry in range(self.max_retries_per_provider):
                try:
                    # Set as current provider
                    self.current_provider = provider_name
                    
                    # Execute operation
                    result = operation_func(provider, *args, **kwargs)
                    
                    # Record successful request
                    provider.record_request()
                    provider.reset_error_count()
                    
                    self.logger.info(f"Successfully executed {operation_name} with {provider_name}")
                    return result
                    
                except RateLimitError as e:
                    self.logger.warning(f"{provider_name} hit rate limit: {e}")
                    provider.status = DataProviderStatus.RATE_LIMITED
                    last_error = e
                    break  # Don't retry, switch to next provider
                    
                except AuthenticationError as e:
                    self.logger.error(f"{provider_name} authentication error: {e}")
                    provider.status = DataProviderStatus.ERROR
                    last_error = e
                    break  # Don't retry, switch to next provider
                    
                except DataNotFoundError as e:
                    # Data not found is not a provider error, return None
                    self.logger.info(f"Data not found with {provider_name}: {e}")
                    return None
                    
                except Exception as e:
                    self.logger.warning(f"{provider_name} error on attempt {retry + 1}: {e}")
                    provider.record_error(e)
                    last_error = e
                    
                    if retry < self.max_retries_per_provider - 1:
                        time.sleep(1)  # Brief delay before retry
                    else:
                        # Max retries reached for this provider
                        break
            
            # Add delay before trying next provider
            if attempt < len(self.provider_order) - 1:
                time.sleep(self.fallback_delay)
        
        # All providers failed
        self.logger.error(f"All providers failed for {operation_name}")
        if last_error:
            raise last_error
        else:
            raise DataProviderError("DataProviderManager", f"All providers failed for {operation_name}")
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock info with provider fallback"""
        def _operation(provider: BaseDataProvider, symbol: str):
            return provider.get_stock_info(symbol)
        
        try:
            return self._try_with_fallback("get_stock_info", _operation, symbol)
        except Exception as e:
            self.logger.error(f"Failed to get stock info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                          interval: str = "1D") -> Optional[pd.DataFrame]:
        """Get historical data with provider fallback"""
        def _operation(provider: BaseDataProvider, symbol: str, start_date: date, 
                      end_date: date, interval: str):
            return provider.get_historical_data(symbol, start_date, end_date, interval)
        
        try:
            return self._try_with_fallback("get_historical_data", _operation, 
                                         symbol, start_date, end_date, interval)
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None
    
    def get_real_time_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time data with provider fallback"""
        def _operation(provider: BaseDataProvider, symbols: List[str]):
            return provider.get_real_time_data(symbols)
        
        try:
            return self._try_with_fallback("get_real_time_data", _operation, symbols)
        except Exception as e:
            self.logger.error(f"Failed to get real-time data: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search stocks with provider fallback"""
        def _operation(provider: BaseDataProvider, query: str):
            return provider.search_stocks(query)
        
        try:
            result = self._try_with_fallback("search_stocks", _operation, query)
            return result if result else []
        except Exception as e:
            self.logger.error(f"Failed to search stocks for '{query}': {e}")
            return []
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            'current_provider': self.current_provider,
            'total_providers': len(self.providers),
            'provider_order': self.provider_order,
            'providers': {}
        }
        
        for name, provider in self.providers.items():
            status['providers'][name] = provider.get_status_info()
        
        return status
    
    def force_switch_provider(self, provider_name: str) -> bool:
        """Manually switch to a specific provider"""
        if provider_name not in self.providers:
            self.logger.error(f"Provider {provider_name} not found")
            return False
        
        provider = self.providers[provider_name]
        if not provider.is_available():
            self.logger.error(f"Provider {provider_name} is not available")
            return False
        
        self.current_provider = provider_name
        self.logger.info(f"Manually switched to provider: {provider_name}")
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health_status = {
            'overall_status': 'healthy',
            'available_providers': 0,
            'total_providers': len(self.providers),
            'current_provider': self.current_provider,
            'provider_health': {}
        }
        
        for name, provider in self.providers.items():
            try:
                # Simple health check - try to get provider status
                provider_status = provider.get_status_info()
                is_healthy = provider.is_available()
                
                health_status['provider_health'][name] = {
                    'status': provider_status['status'],
                    'is_healthy': is_healthy,
                    'error_count': provider_status['error_count'],
                    'requests_today': provider_status['requests_today']
                }
                
                if is_healthy:
                    health_status['available_providers'] += 1
                    
            except Exception as e:
                health_status['provider_health'][name] = {
                    'status': 'error',
                    'is_healthy': False,
                    'error': str(e)
                }
        
        # Determine overall status
        if health_status['available_providers'] == 0:
            health_status['overall_status'] = 'critical'
        elif health_status['available_providers'] < health_status['total_providers'] / 2:
            health_status['overall_status'] = 'degraded'
        
        return health_status
    
    def reset_provider_status(self, provider_name: str = None):
        """Reset error counts and status for providers"""
        if provider_name:
            if provider_name in self.providers:
                self.providers[provider_name].reset_error_count()
                self.logger.info(f"Reset status for {provider_name}")
        else:
            for provider in self.providers.values():
                provider.reset_error_count()
            self.logger.info("Reset status for all providers")

# Global instance
provider_manager = DataProviderManager()