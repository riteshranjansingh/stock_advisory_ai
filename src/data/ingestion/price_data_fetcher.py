"""
Price Data Fetcher V2 - Using Provider System
Enhanced version with multiple data provider support and intelligent fallback
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.database import db_manager
from config.settings import STOCK_UNIVERSE, DATA_UPDATE_CONFIG
from src.data.providers.provider_manager import provider_manager
from src.data.providers.fyers_provider import FyersProvider
from src.data.providers.sample_provider import SampleDataProvider

class PriceDataFetcherV2:
    """Enhanced price data fetcher using multiple providers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.min_market_cap = STOCK_UNIVERSE['min_market_cap']
        self.target_stock_count = STOCK_UNIVERSE['target_stock_count']
        
        # Initialize providers
        self._setup_providers()
        
        self.logger.info("Enhanced Price Data Fetcher V2 initialized")
    
    def _setup_providers(self):
        """Set up data providers"""
        # Register Sample Data Provider (always available as fallback)
        sample_provider = SampleDataProvider()
        provider_manager.register_provider(sample_provider)
        
        # Note: Fyers provider would be registered when user provides credentials
        # self._register_fyers_provider(credentials)
        
        self.logger.info("Data providers registered")
    
    def register_fyers_provider(self, client_id: str, access_token: str) -> bool:
        """Register Fyers provider with credentials"""
        try:
            fyers_provider = FyersProvider()
            credentials = {
                'client_id': client_id,
                'access_token': access_token
            }
            
            success = provider_manager.register_provider(fyers_provider, credentials)
            
            if success:
                self.logger.info("Fyers provider registered successfully")
            else:
                self.logger.error("Failed to register Fyers provider")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error registering Fyers provider: {e}")
            return False
    
    def get_available_stocks(self) -> List[str]:
        """Get list of available stocks from current provider"""
        try:
            active_provider = provider_manager.get_active_provider()
            
            if hasattr(active_provider, 'get_available_symbols'):
                symbols = active_provider.get_available_symbols()
                self.logger.info(f"Found {len(symbols)} available symbols from {active_provider.name}")
                return symbols
            else:
                # Fallback to predefined list
                default_symbols = [
                    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
                    'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK'
                ]
                return default_symbols[:self.target_stock_count]
                
        except Exception as e:
            self.logger.error(f"Error getting available stocks: {e}")
            return []
    
    def fetch_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch stock information using provider system"""
        try:
            stock_info = provider_manager.get_stock_info(symbol)
            
            if stock_info and stock_info.get('market_cap', 0) >= self.min_market_cap:
                self.logger.info(f"Fetched info for {symbol}: {stock_info['name']}")
                return stock_info
            elif stock_info:
                self.logger.info(f"Skipping {symbol} - market cap below threshold")
                return None
            else:
                self.logger.warning(f"No stock info found for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching stock info for {symbol}: {e}")
            return None
    
    def fetch_historical_data(self, symbol: str, start_date: date, end_date: date, 
                            interval: str = "1D") -> Optional[pd.DataFrame]:
        """Fetch historical data using provider system"""
        try:
            self.logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            data = provider_manager.get_historical_data(symbol, start_date, end_date, interval)
            
            if data is not None and len(data) > 0:
                # Standardize column names
                data = self._standardize_price_data(data)
                self.logger.info(f"Fetched {len(data)} records for {symbol}")
                return data
            else:
                self.logger.warning(f"No historical data available for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def fetch_real_time_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch real-time data using provider system"""
        try:
            self.logger.info(f"Fetching real-time data for {len(symbols)} symbols")
            
            data = provider_manager.get_real_time_data(symbols)
            
            if data:
                self.logger.info(f"Fetched real-time data for {len(data)} symbols")
                return data
            else:
                self.logger.warning("No real-time data available")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error fetching real-time data: {e}")
            return {}
    
    def _standardize_price_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Standardize price data format"""
        # Ensure consistent column names
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high', 
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adjusted_close'
        }
        
        # Apply column mapping
        for old_col, new_col in column_mapping.items():
            if old_col in data.columns:
                data = data.rename(columns={old_col: new_col})
        
        # Ensure required columns exist
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                self.logger.error(f"Missing required column: {col}")
                return pd.DataFrame()  # Return empty DataFrame
        
        # Add adjusted_close if not present
        if 'adjusted_close' not in data.columns:
            data['adjusted_close'] = data['close']
        
        # Convert date column
        if data['date'].dtype == 'object':
            data['date'] = pd.to_datetime(data['date']).dt.date
        
        # Remove any null values
        data = data.dropna()
        
        return data
    
    def store_stock_info(self, stock_info: Dict[str, Any]) -> bool:
        """Store stock information in database"""
        try:
            success = db_manager.add_stock(
                symbol=stock_info['symbol'],
                name=stock_info['name'],
                sector=stock_info.get('sector', 'Unknown'),
                market_cap=stock_info.get('market_cap', 0)
            )
            
            if success:
                self.logger.info(f"Stored stock info for {stock_info['symbol']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error storing stock info for {stock_info['symbol']}: {e}")
            return False
    
    def store_price_data(self, symbol: str, price_data: pd.DataFrame) -> bool:
        """Store price data in database"""
        try:
            # Get stock ID
            stock_info = db_manager.get_stock_by_symbol(symbol)
            if not stock_info:
                self.logger.error(f"Stock {symbol} not found in database")
                return False
            
            stock_id = stock_info['id']
            
            # Store price data
            with db_manager.get_connection() as conn:
                stored_count = 0
                for _, row in price_data.iterrows():
                    try:
                        conn.execute('''
                            INSERT OR REPLACE INTO price_data 
                            (stock_id, date, open_price, high_price, low_price, close_price, volume, adjusted_close)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            stock_id,
                            row['date'],
                            float(row['open']),
                            float(row['high']),
                            float(row['low']),
                            float(row['close']),
                            int(row['volume']),
                            float(row['adjusted_close']) if pd.notna(row['adjusted_close']) else float(row['close'])
                        ))
                        stored_count += 1
                    except Exception as row_error:
                        self.logger.warning(f"Error storing row for {symbol}: {row_error}")
                        continue
                
                conn.commit()
            
            self.logger.info(f"Stored {stored_count}/{len(price_data)} price records for {symbol}")
            return stored_count > 0
            
        except Exception as e:
            self.logger.error(f"Error storing price data for {symbol}: {e}")
            return False
    
    def update_single_stock(self, symbol: str, days_back: int = 365) -> Dict[str, Any]:
        """Update data for a single stock"""
        result = {
            'symbol': symbol,
            'success': False,
            'info_updated': False,
            'price_data_updated': False,
            'records_stored': 0,
            'error': None
        }
        
        try:
            self.logger.info(f"Updating data for {symbol}")
            
            # Fetch and store stock info
            stock_info = self.fetch_stock_info(symbol)
            if stock_info:
                result['info_updated'] = self.store_stock_info(stock_info)
            else:
                result['error'] = "Could not fetch stock info"
                return result
            
            # Fetch and store price data
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            price_data = self.fetch_historical_data(symbol, start_date, end_date)
            if price_data is not None and len(price_data) > 0:
                result['price_data_updated'] = self.store_price_data(symbol, price_data)
                result['records_stored'] = len(price_data)
            else:
                result['error'] = "Could not fetch price data"
                return result
            
            result['success'] = result['info_updated'] and result['price_data_updated']
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error updating {symbol}: {e}")
        
        return result
    
    def update_multiple_stocks(self, symbols: List[str] = None, days_back: int = 365) -> Dict[str, Any]:
        """Update data for multiple stocks"""
        if symbols is None:
            symbols = self.get_available_stocks()
        
        results = {
            'total_symbols': len(symbols),
            'successful': 0,
            'failed': 0,
            'stock_results': {},
            'provider_status': provider_manager.get_provider_status()
        }
        
        self.logger.info(f"Starting bulk update for {len(symbols)} stocks")
        
        for i, symbol in enumerate(symbols, 1):
            self.logger.info(f"Processing {symbol} ({i}/{len(symbols)})")
            
            stock_result = self.update_single_stock(symbol, days_back)
            results['stock_results'][symbol] = stock_result
            
            if stock_result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        self.logger.info(f"Bulk update completed. Success: {results['successful']}, Failed: {results['failed']}")
        
        return results
    
    def get_latest_price_data(self, symbol: str, days: int = 200) -> Optional[pd.DataFrame]:
        """Get latest price data for a stock from database"""
        try:
            stock_info = db_manager.get_stock_by_symbol(symbol)
            if not stock_info:
                return None
            
            with db_manager.get_connection() as conn:
                query = '''
                    SELECT date, open_price as open, high_price as high, 
                           low_price as low, close_price as close, volume, adjusted_close
                    FROM price_data 
                    WHERE stock_id = ? 
                    ORDER BY date DESC 
                    LIMIT ?
                '''
                
                result = conn.execute(query, (stock_info['id'], days)).fetchall()
                
                if not result:
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame([dict(row) for row in result])
                df = df.sort_values('date').reset_index(drop=True)
                df['date'] = pd.to_datetime(df['date'])
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting price data for {symbol}: {e}")
            return None
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all data providers"""
        return provider_manager.get_provider_status()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = provider_manager.health_check()
        
        # Add database health check
        db_health = db_manager.health_check()
        health_status['database'] = db_health
        
        return health_status

# Global instance
price_fetcher_v2 = PriceDataFetcherV2()