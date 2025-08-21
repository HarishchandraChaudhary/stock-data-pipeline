import os
import logging
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
from retry import retry

logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self.session = requests.Session()
        
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is required")
        
        self.default_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    
    @retry(tries=3, delay=2)
    def fetch_daily_data(self, symbol: str) -> Dict[str, Any]:
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'compact',
            'datatype': 'json'
        }
        
        try:
            logger.info(f"Fetching daily data for {symbol}")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            
            if 'Note' in data:
                logger.warning(f"API Note: {data['Note']}")
                time.sleep(60)
                return self.fetch_daily_data(symbol)
            
            logger.info(f"Successfully fetched data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
    
    def parse_stock_data(self, raw_data: Dict[str, Any], symbol: str) -> List[Dict[str, Any]]:
        try:
            parsed_data = []
            time_series_key = 'Time Series (Daily)'
            
            if time_series_key not in raw_data:
                logger.error(f"No time series data found for {symbol}")
                return parsed_data
            
            time_series = raw_data[time_series_key]
            
            for timestamp, values in time_series.items():
                try:
                    record = {
                        'symbol': symbol.upper(),
                        'timestamp': datetime.strptime(timestamp, '%Y-%m-%d'),
                        'open_price': float(values.get('1. open', 0)) or None,
                        'high_price': float(values.get('2. high', 0)) or None,
                        'low_price': float(values.get('3. low', 0)) or None,
                        'close_price': float(values.get('4. close', 0)) or None,
                        'volume': int(values.get('5. volume', 0)) or None
                    }
                    
                    if record['close_price'] and record['close_price'] > 0:
                        parsed_data.append(record)
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing record for {symbol} at {timestamp}: {str(e)}")
                    continue
            
            logger.info(f"Parsed {len(parsed_data)} records for {symbol}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing stock data for {symbol}: {str(e)}")
            return []
    
    def fetch_multiple_symbols(self, symbols: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        if symbols is None:
            symbols = self.default_symbols
        
        all_data = {}
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"Processing symbol {symbol} ({i+1}/{len(symbols)})")
                
                raw_data = self.fetch_daily_data(symbol)
                parsed_data = self.parse_stock_data(raw_data, symbol)
                all_data[symbol] = parsed_data
                
                # Rate limiting
                if i < len(symbols) - 1:
                    logger.info("Waiting 12 seconds before next request...")
                    time.sleep(12)
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {str(e)}")
                all_data[symbol] = []
                continue
        
        return all_data

stock_fetcher = StockDataFetcher()
