"""
Enhanced Data Provider Manager V2
Intelligent provider management with manual selection, failover, and health monitoring
"""

from typing import Dict, List, Optional, Any, Type
from datetime import datetime, date, timedelta
import pandas as pd
import logging
import time
import threading
from enum import Enum
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.providers.base_provider import (
    BaseDataProvider, DataProviderStatus, DataProviderPriority,
    DataProviderError, RateLimitError, AuthenticationError, DataNotFoundError
)

# Import the new configuration
try:
    from config.provider_config import provider_config
except ImportError:
    # Fallback configuration if config file not found
    class MockConfig:
        def get_default_provider(self): return 'fyers'
        def get_provider_priority(self): return ['fyers', 'shoonya', 'mstock']
        def is_failover_enabled(self): return True
        def get_retry_attempts(self): return 3
        def should_stay_switched(self): return True
        def is_health_monitoring_enabled(self): return True
        def should_notify_recovery(self): return True
        def get_background_check_interval(self): return 300
    
    provider_config = MockConfig()

class ProviderHealth(Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"

class EnhancedDataProviderManager:
    """
    Enhanced Data Provider Manager with intelligent failover and manual selection
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseDataProvider] = {}
        self.provider_order: List[str] = []
        
        # Manual provider selection
        self.preferred_provider: Optional[str] = None
        self.current_provider: Optional[str] = None
        
        # Health monitoring
        self.provider_health: Dict[str, ProviderHealth] = {}
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_time: Dict[str, datetime] = {}
        self.recovery_notified: Dict[str, bool] = {}
        
        # Retry logic
        self.retry_attempts: Dict[str, int] = {}
        self.max_retries = provider_config.get_retry_attempts()
        
        # Background monitoring
        self.health_monitor_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Auto-initialization flag
        self._initialized = False
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Enhanced Data Provider Manager V2 initialized")
    
    def _ensure_providers_initialized(self):
        """Ensure providers are registered and initialized (auto-registration)"""
        if self._initialized and len(self.providers) > 0:
            return True
        
        try:
            self.logger.info("🔧 Auto-registering providers...")
            
            # Import providers
            from src.data.providers.fyers_provider import FyersProvider
            from src.data.providers.shoonya_provider import ShoonyaProvider
            from src.data.providers.mstock_provider import MStockProvider
            from src.data.providers.sample_provider import SampleDataProvider
            
            # Register providers in priority order
            providers_to_register = [
                ("Fyers", FyersProvider),
                ("Shoonya", ShoonyaProvider), 
                ("MStock", MStockProvider),
                ("Sample", SampleDataProvider)  # Always-available fallback
            ]
            
            registered_count = 0
            
            for provider_name, provider_class in providers_to_register:
                try:
                    # Create provider instance
                    provider = provider_class()
                    
                    # Register with manager
                    success = self.register_provider(provider)
                    
                    if success:
                        registered_count += 1
                        self.logger.debug(f"   ✅ {provider_name} auto-registered")
                    else:
                        self.logger.debug(f"   ⚠️  {provider_name} auto-registration failed")
                        
                except Exception as e:
                    self.logger.debug(f"   ❌ {provider_name} auto-registration error: {e}")
                    continue
            
            if registered_count > 0:
                self.logger.info(f"✅ Auto-registered {registered_count} providers")
                
                # Perform startup health check
                if provider_config.is_health_monitoring_enabled():
                    self.startup_health_check()
                
                self._initialized = True
                return True
            else:
                self.logger.warning("❌ No providers could be auto-registered")
                return False
                
        except Exception as e:
            self.logger.error(f"Auto-registration failed: {e}")
            return False

    def register_provider(self, provider: BaseDataProvider, credentials: Dict[str, str] = None) -> bool:
        """Register a new data provider"""
        try:
            # Authenticate if credentials provided
            if credentials:
                auth_success = provider.authenticate(credentials)
                if not auth_success:
                    self.logger.error(f"Failed to authenticate {provider.name}")
                    return False
            
            # Add to provider registry
            self.providers[provider.name.lower()] = provider
            
            # Initialize health tracking
            self.provider_health[provider.name.lower()] = ProviderHealth.UNKNOWN
            self.failure_counts[provider.name.lower()] = 0
            self.retry_attempts[provider.name.lower()] = 0
            self.recovery_notified[provider.name.lower()] = False
            
            # Update provider order based on configuration
            self._update_provider_order()
            
            # Set current provider if not set
            if not self.current_provider:
                self.current_provider = provider_config.get_default_provider()
            
            self.logger.info(f"Registered {provider.name} provider")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering {provider.name}: {e}")
            return False
    
    def _update_provider_order(self):
        """Update provider order based on configuration"""
        config_order = provider_config.get_provider_priority()
        
        # Only include registered providers in the order
        self.provider_order = [
            name for name in config_order 
            if name.lower() in self.providers
        ]
        
        self.logger.debug(f"Provider order updated: {self.provider_order}")
    
    def set_preferred_provider(self, provider_name: str) -> bool:
        """
        Manually set preferred provider
        
        Args:
            provider_name: Name of provider to prefer
            
        Returns:
            bool: Success status
        """
        # Ensure providers are initialized
        if not self._ensure_providers_initialized():
            self.logger.error("Failed to initialize providers")
            return False
        
        provider_name = provider_name.lower()
        
        if provider_name not in self.providers:
            self.logger.error(f"Provider {provider_name} not registered")
            return False
        
        self.preferred_provider = provider_name
        self.current_provider = provider_name
        
        # Reset retry counts for manual switch
        self.retry_attempts[provider_name] = 0
        
        self.logger.info(f"✅ Manually switched to preferred provider: {provider_name}")
        return True
    
    def get_current_provider_name(self) -> Optional[str]:
        """Get name of currently active provider"""
        return self.current_provider
    
    def get_active_provider(self) -> Optional[BaseDataProvider]:
        """Get the currently active provider instance"""
        # Ensure providers are initialized
        if not self._ensure_providers_initialized():
            self.logger.error("Failed to initialize providers")
            return None
        
        if not self.current_provider or self.current_provider not in self.providers:
            self._select_best_provider()
        
        if self.current_provider:
            return self.providers[self.current_provider]
        
        return None
    
    def _select_best_provider(self) -> bool:
        """
        Select the best available provider using intelligent logic
        
        Priority:
        1. Preferred provider (if set and healthy)
        2. Default provider (if healthy) 
        3. Next healthy provider in priority order
        4. Any available provider
        """
        # Check preferred provider first
        if self.preferred_provider and self._is_provider_healthy(self.preferred_provider):
            if self.current_provider != self.preferred_provider:
                self.logger.info(f"Switching to preferred provider: {self.preferred_provider}")
                self.current_provider = self.preferred_provider
            return True
        
        # Check default provider
        default_provider = provider_config.get_default_provider()
        if (not self.preferred_provider and 
            default_provider in self.providers and 
            self._is_provider_healthy(default_provider)):
            
            if self.current_provider != default_provider:
                self.logger.info(f"Using default provider: {default_provider}")
                self.current_provider = default_provider
            return True
        
        # Fall back to priority order
        for provider_name in self.provider_order:
            if self._is_provider_healthy(provider_name):
                if self.current_provider != provider_name:
                    self.logger.info(f"Switching to healthy provider: {provider_name}")
                    self.current_provider = provider_name
                return True
        
        # Last resort: any available provider
        for provider_name, provider in self.providers.items():
            if provider.is_available():
                if self.current_provider != provider_name:
                    self.logger.warning(f"Using last resort provider: {provider_name}")
                    self.current_provider = provider_name
                return True
        
        self.logger.error("No available providers found")
        self.current_provider = None
        return False
    
    def _is_provider_healthy(self, provider_name: str) -> bool:
        """Check if a provider is healthy"""
        if provider_name not in self.providers:
            return False
        
        # Check health status
        health = self.provider_health.get(provider_name, ProviderHealth.UNKNOWN)
        if health in [ProviderHealth.FAILED]:
            return False
        
        # Check if provider is available
        provider = self.providers[provider_name]
        return provider.is_available()
    
    def _try_with_intelligent_fallback(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Execute operation with intelligent fallback logic
        
        Features:
        - Respects preferred provider
        - Implements retry logic
        - Cascades through priority order
        - Health monitoring and recovery
        """
        # Ensure providers are initialized
        if not self._ensure_providers_initialized():
            raise DataProviderError("DataProviderManager", "No providers available - initialization failed")
        
        last_error = None
        
        # Ensure we have a current provider
        if not self._select_best_provider():
            raise DataProviderError("DataProviderManager", "No available providers")
        
        # Try with current provider first
        for attempt in range(self.max_retries + 1):
            current_provider_name = self.current_provider
            current_provider = self.providers[current_provider_name]
            
            try:
                self.logger.debug(f"Trying {operation_name} with {current_provider_name} (attempt {attempt + 1})")
                
                # Execute operation
                result = operation_func(current_provider, *args, **kwargs)
                
                # Success! Reset failure tracking
                self._record_success(current_provider_name)
                
                return result
                
            except RateLimitError as e:
                self.logger.warning(f"{current_provider_name} hit rate limit: {e}")
                self._record_failure(current_provider_name, e)
                last_error = e
                
                # For rate limits, immediately try next provider
                if self._switch_to_next_provider():
                    continue
                else:
                    break
                    
            except AuthenticationError as e:
                self.logger.error(f"{current_provider_name} authentication error: {e}")
                self._record_failure(current_provider_name, e)
                last_error = e
                
                # For auth errors, immediately try next provider
                if self._switch_to_next_provider():
                    continue
                else:
                    break
                    
            except DataNotFoundError as e:
                # Data not found is not a provider error
                self.logger.debug(f"Data not found with {current_provider_name}: {e}")
                return None
                
            except Exception as e:
                self.logger.warning(f"{current_provider_name} error: {e}")
                self._record_failure(current_provider_name, e)
                last_error = e
                
                # For other errors, retry with same provider first
                if attempt < self.max_retries:
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    # Max retries reached, try next provider
                    if not self._switch_to_next_provider():
                        break
        
        # All providers and retries failed
        self.logger.error(f"All providers failed for {operation_name}")
        if last_error:
            raise last_error
        else:
            raise DataProviderError("DataProviderManager", f"All providers failed for {operation_name}")
    
    def _switch_to_next_provider(self) -> bool:
        """
        Switch to next available provider in priority order
        
        Returns:
            bool: True if successfully switched to another provider
        """
        if not provider_config.is_failover_enabled():
            self.logger.info("Failover disabled, not switching providers")
            return False
        
        current_index = -1
        if self.current_provider in self.provider_order:
            current_index = self.provider_order.index(self.current_provider)
        
        # Try providers after current one
        for i in range(current_index + 1, len(self.provider_order)):
            next_provider = self.provider_order[i]
            if self._is_provider_healthy(next_provider):
                self.logger.info(f"🔄 Switching from {self.current_provider} to {next_provider}")
                self.current_provider = next_provider
                return True
        
        # No healthy providers found in order
        self.logger.error("No healthy providers available for switching")
        return False
    
    def _record_success(self, provider_name: str):
        """Record successful operation for provider"""
        # Reset failure count
        self.failure_counts[provider_name] = 0
        self.retry_attempts[provider_name] = 0
        
        # Update health status
        old_health = self.provider_health.get(provider_name, ProviderHealth.UNKNOWN)
        self.provider_health[provider_name] = ProviderHealth.HEALTHY
        
        # Notify recovery if it was previously failed
        if (old_health == ProviderHealth.FAILED and 
            provider_config.should_notify_recovery() and
            not self.recovery_notified.get(provider_name, False)):
            
            self.logger.info(f"💚 {provider_name} is back online!")
            self.recovery_notified[provider_name] = True
    
    def _record_failure(self, provider_name: str, error: Exception):
        """Record failure for provider"""
        self.failure_counts[provider_name] = self.failure_counts.get(provider_name, 0) + 1
        self.last_failure_time[provider_name] = datetime.now()
        
        # Update health status based on failure count
        failure_count = self.failure_counts[provider_name]
        if failure_count >= 5:  # Configurable threshold
            self.provider_health[provider_name] = ProviderHealth.FAILED
            self.recovery_notified[provider_name] = False  # Reset for future recovery
        elif failure_count >= 3:
            self.provider_health[provider_name] = ProviderHealth.DEGRADED
        
        self.logger.debug(f"Recorded failure for {provider_name}: {failure_count} failures")
    
    def startup_health_check(self):
        """Perform health check on all providers at startup"""
        if not provider_config.is_health_monitoring_enabled():
            return
        
        self.logger.info("🏥 Performing startup health check...")
        
        for provider_name, provider in self.providers.items():
            try:
                if provider.is_available():
                    self.provider_health[provider_name] = ProviderHealth.HEALTHY
                    status = "🟢 Healthy"
                else:
                    self.provider_health[provider_name] = ProviderHealth.FAILED
                    status = "🔴 Failed"
                
                self.logger.info(f"   {provider_name}: {status}")
                
            except Exception as e:
                self.provider_health[provider_name] = ProviderHealth.FAILED
                self.logger.warning(f"   {provider_name}: 🔴 Failed ({e})")
        
        # Set initial provider
        self._select_best_provider()
        if self.current_provider:
            self.logger.info(f"🚀 Starting with {self.current_provider}")
    
    # Public API methods with intelligent fallback
    def get_stock_info(self, symbol: str, exchange: str = 'NSE') -> Optional[Dict[str, Any]]:
        """Get stock info with automatic symbol normalization - FIXED VERSION"""
        def _operation(provider: BaseDataProvider, symbol: str, exchange: str):
            # Use the provider's method directly - let IT handle symbol conversion
            result = provider.get_stock_info(symbol)
            
            # Ensure clean symbol in result
            if result:
                result['symbol'] = symbol  # Always return clean symbol
                result['exchange'] = exchange
                # Keep provider_symbol for debugging if available
                if 'provider_symbol' not in result:
                    result['provider_symbol'] = provider.normalize_symbol(symbol, exchange) if hasattr(provider, 'normalize_symbol') else symbol
            
            return result
        
        try:
            # Ensure providers are initialized
            if not self._ensure_providers_initialized():
                self.logger.error("Failed to initialize providers")
                return None
            
            return self._try_with_intelligent_fallback("get_stock_info", _operation, symbol, exchange)
        except Exception as e:
            self.logger.error(f"Failed to get stock info for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol: str, start_date: date, end_date: date, 
                        interval: str = "1D", exchange: str = 'NSE') -> Optional[pd.DataFrame]:
        """Get historical data with automatic symbol normalization - FIXED VERSION"""
        def _operation(provider: BaseDataProvider, symbol: str, start_date: date, 
                    end_date: date, interval: str, exchange: str):
            
            # CRITICAL FIX: Use provider's method directly, don't bypass it!
            data = provider.get_historical_data(symbol, start_date, end_date, interval)
            
            # Ensure clean symbol in result DataFrame
            if data is not None and not data.empty:
                data = data.copy()
                # Add clean symbol column if not present
                if 'symbol' not in data.columns:
                    data['symbol'] = symbol
                else:
                    # Ensure all symbols are clean
                    data['symbol'] = symbol
                
                # Add debugging info
                data['exchange'] = exchange
                if hasattr(provider, 'normalize_symbol'):
                    provider_symbol = provider.normalize_symbol(symbol, exchange)
                    data['provider_symbol'] = provider_symbol
            
            return data
        
        try:
            # Ensure providers are initialized
            if not self._ensure_providers_initialized():
                self.logger.error("Failed to initialize providers")
                return None
            
            return self._try_with_intelligent_fallback("get_historical_data", _operation, 
                                                    symbol, start_date, end_date, interval, exchange)
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None
    
    def get_real_time_data(self, symbols: List[str], exchange: str = 'NSE') -> Optional[Dict[str, Dict[str, Any]]]:
        """Get real-time data with automatic symbol normalization - FIXED VERSION"""
        def _operation(provider: BaseDataProvider, symbols: List[str], exchange: str):
            
            # CRITICAL FIX: Use provider's method directly with clean symbols
            provider_data = provider.get_real_time_data(symbols)
            
            if not provider_data:
                return None
            
            # Ensure all results have clean symbols
            normalized_data = {}
            for symbol in symbols:
                # Look for this symbol in provider data (provider handles symbol conversion internally)
                symbol_data = None
                
                # Provider might return data with clean symbols or provider-specific symbols
                for key, data in provider_data.items():
                    # Check if this data is for our symbol
                    if (key == symbol or 
                        (hasattr(provider, 'denormalize_symbol') and 
                        provider.denormalize_symbol(key).upper() == symbol.upper())):
                        symbol_data = data.copy()
                        break
                
                if symbol_data:
                    # Ensure clean symbol in result
                    symbol_data['symbol'] = symbol
                    symbol_data['exchange'] = exchange
                    normalized_data[symbol] = symbol_data
            
            return normalized_data
        
        try:
            # Ensure providers are initialized
            if not self._ensure_providers_initialized():
                self.logger.error("Failed to initialize providers")
                return None
            
            return self._try_with_intelligent_fallback("get_real_time_data", _operation, symbols, exchange)
        except Exception as e:
            self.logger.error(f"Failed to get real-time data: {e}")
            return None


    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search stocks with symbol normalization - FIXED VERSION"""
        def _operation(provider: BaseDataProvider, query: str):
            # Use provider's search method directly
            results = provider.search_stocks(query)
            
            # Ensure all results have clean symbols
            if results:
                for result in results:
                    if 'symbol' in result:
                        # If provider returned provider-specific symbol, clean it
                        if hasattr(provider, 'denormalize_symbol'):
                            clean_symbol = provider.denormalize_symbol(result['symbol'])
                            original_symbol = result['symbol']
                            result['symbol'] = clean_symbol
                            result['provider_symbol'] = original_symbol
                        # Ensure symbol is clean
                        result['symbol'] = result['symbol'].upper()
            
            return results
        
        try:
            # Ensure providers are initialized
            if not self._ensure_providers_initialized():
                return []
            
            result = self._try_with_intelligent_fallback("search_stocks", _operation, query)
            return result if result else []
        except Exception as e:
            self.logger.error(f"Failed to search stocks for '{query}': {e}")
            return []
    
    def get_symbol_info(self, symbol: str, exchange: str = 'NSE') -> Dict[str, str]:
        """Get symbol mapping information for debugging - NEW METHOD"""
        try:
            if not self._ensure_providers_initialized():
                return {}
            
            current_provider = self.get_active_provider()
            if not current_provider:
                return {}
            
            info = {
                'clean_symbol': symbol,
                'provider_name': current_provider.name,
                'exchange': exchange
            }
            
            # Test normalization if available
            if hasattr(current_provider, 'normalize_symbol'):
                try:
                    provider_symbol = current_provider.normalize_symbol(symbol, exchange)
                    info['provider_symbol'] = provider_symbol
                    
                    if hasattr(current_provider, 'denormalize_symbol'):
                        clean_back = current_provider.denormalize_symbol(provider_symbol)
                        info['normalized_back'] = clean_back
                        info['consistent'] = symbol.upper() == clean_back.upper()
                    else:
                        info['consistent'] = True
                except Exception as e:
                    info['normalization_error'] = str(e)
                    info['consistent'] = False
            else:
                info['normalization_available'] = False
                info['consistent'] = True
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting symbol info: {e}")
            return {'error': str(e)}

    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all providers"""
        # Ensure providers are initialized
        if not self._ensure_providers_initialized():
            # Return basic status even if initialization failed
            return {
                'current_provider': None,
                'preferred_provider': self.preferred_provider,
                'total_providers': 0,
                'provider_order': [],
                'failover_enabled': provider_config.is_failover_enabled(),
                'health_monitoring': provider_config.is_health_monitoring_enabled(),
                'providers': {},
                'initialization_failed': True
            }
        
        status = {
            'current_provider': self.current_provider,
            'preferred_provider': self.preferred_provider,
            'total_providers': len(self.providers),
            'provider_order': self.provider_order,
            'failover_enabled': provider_config.is_failover_enabled(),
            'health_monitoring': provider_config.is_health_monitoring_enabled(),
            'providers': {}
        }
        
        for name, provider in self.providers.items():
            provider_status = provider.get_status_info()
            provider_status.update({
                'health': self.provider_health.get(name, ProviderHealth.UNKNOWN).value,
                'failure_count': self.failure_counts.get(name, 0),
                'last_failure': self.last_failure_time.get(name),
                'recovery_notified': self.recovery_notified.get(name, False)
            })
            status['providers'][name] = provider_status
        
        return status
    
    def reset_provider_health(self, provider_name: str = None):
        """Reset health status and failure counts"""
        if provider_name:
            if provider_name in self.providers:
                self.failure_counts[provider_name] = 0
                self.retry_attempts[provider_name] = 0
                self.provider_health[provider_name] = ProviderHealth.UNKNOWN
                self.recovery_notified[provider_name] = False
                self.logger.info(f"Reset health status for {provider_name}")
        else:
            # Reset all providers
            for name in self.providers:
                self.failure_counts[name] = 0
                self.retry_attempts[name] = 0
                self.provider_health[name] = ProviderHealth.UNKNOWN
                self.recovery_notified[name] = False
            self.logger.info("Reset health status for all providers")

# Global enhanced instance
enhanced_provider_manager = EnhancedDataProviderManager()

# Convenience functions for backward compatibility
def get_provider_manager():
    """Get the enhanced provider manager instance"""
    return enhanced_provider_manager

# Example usage
if __name__ == "__main__":
    print("🚀 Testing Enhanced Provider Manager")
    print("=" * 50)
    
    manager = EnhancedDataProviderManager()
    
    # This would be done with real providers in practice
    print("Enhanced Provider Manager created successfully!")
    print(f"Default provider: {provider_config.get_default_provider()}")
    print(f"Priority order: {provider_config.get_provider_priority()}")
    print(f"Failover enabled: {provider_config.is_failover_enabled()}")
    print(f"Retry attempts: {provider_config.get_retry_attempts()}")