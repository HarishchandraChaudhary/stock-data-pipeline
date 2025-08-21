-- Create stock data table
CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10, 4),
    high_price DECIMAL(10, 4),
    low_price DECIMAL(10, 4),
    close_price DECIMAL(10, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_symbol_timestamp ON stock_data(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_stock_created_at ON stock_data(created_at);

-- Create a view for latest stock prices
CREATE OR REPLACE VIEW latest_stock_prices AS
SELECT DISTINCT ON (symbol) 
    symbol,
    timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    created_at
FROM stock_data
ORDER BY symbol, timestamp DESC;

-- Create error logging table
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id SERIAL PRIMARY KEY,
    dag_id VARCHAR(100),
    task_id VARCHAR(100),
    execution_date TIMESTAMP,
    log_level VARCHAR(20),
    message TEXT,
    error_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
