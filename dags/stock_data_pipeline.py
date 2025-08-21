import os
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

import sys
sys.path.append('/opt/airflow/scripts')

from scripts.stock_fetcher import stock_fetcher
from scripts.database import db_manager

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']

def test_database_connection(**context):
    try:
        if db_manager.test_connection():
            logger.info("Database connection test successful")
            return "success"
        else:
            raise Exception("Database connection test failed")
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        raise

def fetch_and_process_stock_data(**context):
    try:
        logger.info(f"Starting data fetch for symbols: {STOCK_SYMBOLS}")
        
        all_stock_data = stock_fetcher.fetch_multiple_symbols(symbols=STOCK_SYMBOLS)
        
        total_records = 0
        successful_symbols = []
        failed_symbols = []
        
        for symbol, data in all_stock_data.items():
            try:
                if data:
                    records_inserted = db_manager.insert_stock_data(data)
                    total_records += records_inserted
                    successful_symbols.append(symbol)
                    logger.info(f"Processed {records_inserted} records for {symbol}")
                else:
                    failed_symbols.append(symbol)
                    logger.warning(f"No data received for {symbol}")
                    
            except Exception as e:
                failed_symbols.append(symbol)
                logger.error(f"Failed to process data for {symbol}: {str(e)}")
        
        summary = {
            'total_records_inserted': total_records,
            'successful_symbols': successful_symbols,
            'failed_symbols': failed_symbols,
            'success_rate': len(successful_symbols) / len(STOCK_SYMBOLS) * 100
        }
        
        logger.info(f"Data processing summary: {summary}")
        
        if len(failed_symbols) > len(STOCK_SYMBOLS) * 0.5:
            raise Exception(f"Too many failures: {len(failed_symbols)}/{len(STOCK_SYMBOLS)} symbols failed")
        
        return summary
        
    except Exception as e:
        logger.error(f"Critical error in data processing: {str(e)}")
        raise

dag = DAG(
    'stock_data_pipeline',
    default_args=default_args,
    description='Stock Market Data Pipeline',
    schedule_interval=timedelta(hours=6),
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=['stock-data', 'etl', 'finance'],
)

test_db_task = PythonOperator(
    task_id='test_db_connection',
    python_callable=test_database_connection,
    dag=dag,
)

fetch_data_task = PythonOperator(
    task_id='fetch_and_process_data',
    python_callable=fetch_and_process_stock_data,
    dag=dag,
)

test_db_task >> fetch_data_task
