"""
Enhanced Provider Configuration
Centralized configuration for all data providers with intelligent failover
"""

import os
from typing import Dict, List, Any
from pathlib import Path

# Provider priority configurations
PROVIDER_CONFIG = {
    # Default provider selection
    'default_provider': 'fyers',
    
    # Current provider priority (3 brokers)
    'current_priority_order': ['fyers', 'shoonya', 'mstock'],
    
    # Future provider priority (4 brokers - ready for Upstox)
    'future_priority_order': ['fyers', 'upstox', 'shoonya', 'mstock'],
    
    # Failover behavior
    'failover': {
        'enabled': True,                    # Enable automatic failover
        'retry_attempts': 3,                # Try 3 times before switching provider
        'stay_switched': True,              # Stay with working provider (don't auto-switch back)
        'auto_retry_failed': False,         # Don't automatically retry failed providers
        'cascade_on_failure': True,         # Continue to next provider if current fails
    },
    
    # Health monitoring
    'health_monitoring': {
        'startup_check': True,              # Check all providers at startup
        'recovery_notification': True,      # Notify once when failed provider recovers
        'continuous_monitoring': False,     # No spam notifications
        'background_check_interval': 300,   # Check failed providers every 5 minutes
        'max_consecutive_failures': 5,      # Mark as unhealthy after 5 failures
    },
    
    # Rate limiting and performance
    'performance': {
        'request_timeout': 30,              # API request timeout in seconds
        'connection_pool_size': 10,         # Connection pool size per provider
        'max_retries_per_request': 2,       # Retries for individual requests
    },
    
    # Provider-specific settings
    'provider_settings': {
        'fyers': {
            'priority': 1,
            'rate_limit_delay': 1.0,
            'daily_request_limit': 2000,
            'supports': ['historical', 'realtime', 'search', 'fundamentals']
        },
        'shoonya': {
            'priority': 2, 
            'rate_limit_delay': 0.5,
            'daily_request_limit': 3000,
            'supports': ['historical', 'realtime', 'search']
        },
        'mstock': {
            'priority': 3,
            'rate_limit_delay': 1.0,
            'daily_request_limit': 2000,
            'supports': ['historical', 'realtime', 'search']
        },
        # Future provider
        'upstox': {
            'priority': 2,  # Will slot between Fyers and Shoonya
            'rate_limit_delay': 0.8,
            'daily_request_limit': 2500,
            'supports': ['historical', 'realtime', 'search', 'fundamentals']
        }
    }
}

# Environment variable overrides
ENV_OVERRIDES = {
    'PREFERRED_DATA_PROVIDER': 'default_provider',
    'FAILOVER_ENABLED': 'failover.enabled',
    'RETRY_ATTEMPTS': 'failover.retry_attempts',
    'HEALTH_MONITORING': 'health_monitoring.startup_check'
}

class ProviderConfigManager:
    """Manages provider configuration with environment overrides"""
    
    def __init__(self):
        self.config = PROVIDER_CONFIG.copy()
        self._apply_environment_overrides()
        self._validate_config()
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides"""
        for env_var, config_path in ENV_OVERRIDES.items():
            env_value = os.getenv(env_var)
            if env_value:
                self._set_nested_config(config_path, env_value)
    
    def _set_nested_config(self, path: str, value: str):
        """Set nested configuration value from dot notation path"""
        keys = path.split('.')
        current = self.config
        
        # Navigate to parent dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value with type conversion
        final_key = keys[-1]
        if value.lower() in ('true', 'false'):
            current[final_key] = value.lower() == 'true'
        elif value.isdigit():
            current[final_key] = int(value)
        else:
            current[final_key] = value
    
    def _validate_config(self):
        """Validate configuration values"""
        # Ensure default provider is in priority order
        if self.config['default_provider'] not in self.config['current_priority_order']:
            raise ValueError(f"Default provider '{self.config['default_provider']}' not in priority order")
        
        # Ensure retry attempts is reasonable
        if self.config['failover']['retry_attempts'] < 1:
            self.config['failover']['retry_attempts'] = 1
        elif self.config['failover']['retry_attempts'] > 10:
            self.config['failover']['retry_attempts'] = 10
    
    def get_provider_priority(self, include_future: bool = False) -> List[str]:
        """Get provider priority order"""
        if include_future:
            return self.config['future_priority_order'].copy()
        return self.config['current_priority_order'].copy()
    
    def get_provider_settings(self, provider_name: str) -> Dict[str, Any]:
        """Get settings for specific provider"""
        return self.config['provider_settings'].get(provider_name, {})
    
    def is_failover_enabled(self) -> bool:
        """Check if failover is enabled"""
        return self.config['failover']['enabled']
    
    def get_retry_attempts(self) -> int:
        """Get number of retry attempts"""
        return self.config['failover']['retry_attempts']
    
    def should_stay_switched(self) -> bool:
        """Check if should stay with switched provider"""
        return self.config['failover']['stay_switched']
    
    def get_default_provider(self) -> str:
        """Get default provider name"""
        return self.config['default_provider']
    
    def is_health_monitoring_enabled(self) -> bool:
        """Check if health monitoring is enabled"""
        return self.config['health_monitoring']['startup_check']
    
    def should_notify_recovery(self) -> bool:
        """Check if should notify on provider recovery"""
        return self.config['health_monitoring']['recovery_notification']
    
    def get_background_check_interval(self) -> int:
        """Get background health check interval in seconds"""
        return self.config['health_monitoring']['background_check_interval']
    
    def update_config(self, **kwargs):
        """Update configuration at runtime"""
        for key, value in kwargs.items():
            if '.' in key:
                self._set_nested_config(key, str(value))
            else:
                self.config[key] = value
        
        self._validate_config()
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self.config.copy()
    
    def export_config(self, file_path: str = None) -> str:
        """Export current configuration to file"""
        import json
        
        if not file_path:
            file_path = "provider_config_export.json"
        
        with open(file_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        return file_path

# Global configuration instance
provider_config = ProviderConfigManager()

# Convenience functions
def get_default_provider() -> str:
    """Get default provider name"""
    return provider_config.get_default_provider()

def get_provider_priority() -> List[str]:
    """Get current provider priority order"""
    return provider_config.get_provider_priority()

def is_failover_enabled() -> bool:
    """Check if failover is enabled"""
    return provider_config.is_failover_enabled()

def get_retry_attempts() -> int:
    """Get retry attempts count"""
    return provider_config.get_retry_attempts()

# Example usage and testing
if __name__ == "__main__":
    print("🔧 Provider Configuration Test")
    print("=" * 50)
    
    config = ProviderConfigManager()
    
    print(f"Default Provider: {config.get_default_provider()}")
    print(f"Priority Order: {config.get_provider_priority()}")
    print(f"Failover Enabled: {config.is_failover_enabled()}")
    print(f"Retry Attempts: {config.get_retry_attempts()}")
    print(f"Health Monitoring: {config.is_health_monitoring_enabled()}")
    
    print("\nProvider Settings:")
    for provider in config.get_provider_priority():
        settings = config.get_provider_settings(provider)
        print(f"  {provider}: Priority {settings.get('priority', 'N/A')}, Supports: {settings.get('supports', [])}")
    
    print("\nConfiguration loaded successfully! ✅")