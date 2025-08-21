import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'postgres-data')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB', 'stockdata')
        self.user = os.getenv('POSTGRES_USER', 'stockuser')
        self.password = os.getenv('POSTGRES_PASSWORD', 'stockpass123')
        
        self.connection_string = (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        )
        
        self.engine = None
        self.Session = None
        self._init_engine()
    
    def _init_engine(self):
        try:
            self.engine = create_engine(self.connection_string, pool_pre_ping=True)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def insert_stock_data(self, stock_data: List[Dict[str, Any]]) -> int:
        if not stock_data:
            return 0
        
        try:
            df = pd.DataFrame(stock_data)
            df.to_sql('stock_data', self.engine, if_exists='append', index=False)
            logger.info(f"Successfully inserted {len(stock_data)} records")
            return len(stock_data)
        except Exception as e:
            logger.error(f"Failed to insert stock data: {str(e)}")
            return 0

db_manager = DatabaseManager()
