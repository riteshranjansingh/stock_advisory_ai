"""
Database Configuration and Connection Management
Handles SQLite database connection and basic operations
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from config.settings import DATABASE_CONFIG, PROJECT_ROOT

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG['sqlite_db_path']
        self.logger = logging.getLogger(__name__)
        
    def initialize_database(self) -> bool:
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create tables
                self._create_tables(conn)
                conn.commit()
                
            self.logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create all required tables"""
        
        # Stocks table - master list of stocks
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                market_cap REAL,
                listing_date DATE,
                exchange TEXT DEFAULT 'NSE',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Price data table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL,
                date DATE NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                adjusted_close REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (id),
                UNIQUE(stock_id, date)
            )
        ''')
        
        # Fundamental data table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS fundamental_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL,
                quarter TEXT NOT NULL,
                year INTEGER NOT NULL,
                revenue REAL,
                net_profit REAL,
                total_assets REAL,
                total_equity REAL,
                total_debt REAL,
                pe_ratio REAL,
                pb_ratio REAL,
                roe REAL,
                debt_to_equity REAL,
                current_ratio REAL,
                revenue_growth REAL,
                profit_growth REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (id),
                UNIQUE(stock_id, quarter, year)
            )
        ''')
        
        # News and sentiment data
        conn.execute('''
            CREATE TABLE IF NOT EXISTS news_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER,
                date DATE NOT NULL,
                headline TEXT NOT NULL,
                content TEXT,
                source TEXT NOT NULL,
                sentiment_score REAL,
                sentiment_label TEXT,
                relevance_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (id)
            )
        ''')
        
        # Agent decisions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL,
                decision_date DATE NOT NULL,
                timeframe TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                reasoning TEXT,
                technical_score REAL,
                fundamental_score REAL,
                sentiment_score REAL,
                target_price REAL,
                stop_loss REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (id)
            )
        ''')
        
        # Master decisions table (final recommendations)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS master_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL,
                decision_date DATE NOT NULL,
                timeframe TEXT NOT NULL,
                final_action TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                position_size REAL,
                target_price REAL,
                stop_loss REAL,
                reasoning TEXT,
                agent_votes TEXT,
                risk_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (id)
            )
        ''')
        
        # Performance tracking table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS performance_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                stock_id INTEGER NOT NULL,
                entry_date DATE NOT NULL,
                exit_date DATE,
                entry_price REAL NOT NULL,
                exit_price REAL,
                position_size REAL NOT NULL,
                return_percentage REAL,
                absolute_return REAL,
                holding_period_days INTEGER,
                status TEXT DEFAULT 'OPEN',
                exit_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES master_decisions (id),
                FOREIGN KEY (stock_id) REFERENCES stocks (id)
            )
        ''')
        
        # Market regime data
        conn.execute('''
            CREATE TABLE IF NOT EXISTS market_regimes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                regime_type TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                vix_level REAL,
                market_breadth REAL,
                trend_strength REAL,
                volatility_regime TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Technical indicators cache
        conn.execute('''
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL,
                date DATE NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL NOT NULL,
                timeframe TEXT DEFAULT 'daily',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (id),
                UNIQUE(stock_id, date, indicator_name, timeframe)
            )
        ''')
        
        # Create indexes for better performance
        self._create_indexes(conn)
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for better query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_price_data_stock_date ON price_data(stock_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_fundamental_data_stock ON fundamental_data(stock_id, year, quarter)",
            "CREATE INDEX IF NOT EXISTS idx_news_data_stock_date ON news_data(stock_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_agent_decisions_stock_date ON agent_decisions(stock_id, decision_date)",
            "CREATE INDEX IF NOT EXISTS idx_master_decisions_stock_date ON master_decisions(stock_id, decision_date)",
            "CREATE INDEX IF NOT EXISTS idx_performance_tracking_decision ON performance_tracking(decision_id)",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_stock ON technical_indicators(stock_id, date, indicator_name)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock information by symbol"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(
                    "SELECT * FROM stocks WHERE symbol = ?", (symbol,)
                ).fetchone()
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Error fetching stock {symbol}: {e}")
            return None
    
    def add_stock(self, symbol: str, name: str, sector: str = None, 
                  market_cap: float = None) -> bool:
        """Add a new stock to the database"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO stocks 
                    (symbol, name, sector, market_cap, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (symbol, name, sector, market_cap))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error adding stock {symbol}: {e}")
            return False
    
    def get_active_stocks(self) -> List[Dict[str, Any]]:
        """Get all active stocks"""
        try:
            with self.get_connection() as conn:
                results = conn.execute(
                    "SELECT * FROM stocks WHERE is_active = 1 ORDER BY symbol"
                ).fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching active stocks: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            with self.get_connection() as conn:
                # Check if database is accessible
                cursor = conn.execute("SELECT COUNT(*) as count FROM stocks")
                stock_count = cursor.fetchone()['count']
                
                # Check latest price data
                cursor = conn.execute("""
                    SELECT MAX(date) as latest_date, COUNT(*) as price_records 
                    FROM price_data
                """)
                price_info = cursor.fetchone()
                
                return {
                    'status': 'healthy',
                    'stock_count': stock_count,
                    'latest_price_date': price_info['latest_date'],
                    'price_records': price_info['price_records'],
                    'database_path': str(self.db_path)
                }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}

# Create global database instance
db_manager = DatabaseManager()