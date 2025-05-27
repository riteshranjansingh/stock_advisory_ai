"""
AI Trading System - Main Configuration Settings
This file contains all the core settings for the trading system
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "databases"

# Log directory
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, DATABASE_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database settings
DATABASE_CONFIG = {
    'sqlite_db_path': DATABASE_DIR / 'trading_system.db',
    'backup_interval_hours': 24,
    'max_backup_files': 7
}

# Stock universe settings
STOCK_UNIVERSE = {
    'min_market_cap': 5000,  # Minimum market cap in crores
    'target_stock_count': 200,  # Target number of stocks to analyze
    'indices': ['NIFTY500'],  # Focus indices
    'exclude_sectors': [],  # Sectors to exclude (if any)
}

# Data update settings
DATA_UPDATE_CONFIG = {
    'price_data_frequency': 'daily',  # daily, hourly, minute
    'fundamental_data_frequency': 'quarterly',
    'news_data_frequency': 'hourly',
    'market_hours': {
        'start': '09:15',
        'end': '15:30',
        'timezone': 'Asia/Kolkata'
    }
}

# Risk management settings
RISK_MANAGEMENT = {
    'max_single_stock_weight': 0.05,  # 5% max per stock
    'max_sector_weight': 0.25,  # 25% max per sector
    'max_portfolio_drawdown': 0.15,  # 15% max drawdown
    'stop_loss_percentage': 0.08,  # 8% stop loss
    'position_sizing_method': 'volatility_adjusted'
}

# Timeframe settings
TIMEFRAMES = {
    'intraday': {
        'min_holding_minutes': 60,
        'max_holding_hours': 4,
        'signals_per_day': 5
    },
    'swing': {
        'min_holding_days': 1,
        'max_holding_days': 30,
        'signals_per_week': 10
    },
    'investment': {
        'min_holding_days': 30,
        'max_holding_months': 12,
        'signals_per_month': 5
    }
}

# Agent settings
AGENT_CONFIG = {
    'technical_agent': {
        'indicators': ['RSI', 'MACD', 'SMA', 'EMA', 'BB', 'ADX'],
        'lookback_periods': [14, 21, 50, 200],
        'confidence_threshold': 0.6
    },
    'fundamental_agent': {
        'metrics': ['PE', 'ROE', 'DEBT_TO_EQUITY', 'REVENUE_GROWTH', 'PROFIT_GROWTH'],
        'peer_comparison': True,
        'confidence_threshold': 0.7
    },
    'sentiment_agent': {
        'sources': ['news', 'social_media'],
        'sentiment_threshold': 0.1,  # Neutral zone
        'confidence_threshold': 0.5
    }
}

# Backtesting settings
BACKTESTING_CONFIG = {
    'start_date': '2018-01-01',
    'initial_capital': 1000000,  # 10 Lakh for backtesting
    'transaction_cost': 0.001,  # 0.1% transaction cost
    'benchmark': 'NIFTY500',
    'rebalance_frequency': 'weekly'
}

# Logging settings
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'max_file_size_mb': 50,
    'backup_count': 5,
    'log_to_console': True,
    'log_to_file': True
}

# System settings
SYSTEM_CONFIG = {
    'max_concurrent_processes': 4,
    'api_rate_limit_per_minute': 60,
    'data_validation_enabled': True,
    'auto_backup_enabled': True,
    'development_mode': True  # Set to False in production
}

# Phase 1 specific settings (we'll expand in later phases)
PHASE1_CONFIG = {
    'focus_timeframe': 'swing',  # Primary focus on swing trading
    'max_recommendations_per_day': 5,
    'minimum_confidence_score': 0.6,
    'enable_defensive_mode': True
}

print("Configuration loaded successfully!")
print(f"Project root: {PROJECT_ROOT}")
print(f"Database path: {DATABASE_CONFIG['sqlite_db_path']}")