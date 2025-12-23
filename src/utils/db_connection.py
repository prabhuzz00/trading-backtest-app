import pandas as pd
from pymongo import MongoClient
import yaml
import os
from datetime import datetime, timezone, timedelta
from functools import lru_cache
import hashlib
import pickle

# Global connection pool
_mongo_client = None
_database_name = None

def get_mongo_client():
    """Load MongoDB URI from config and return a client with connection pooling."""
    global _mongo_client, _database_name
    
    if _mongo_client is not None:
        return _mongo_client, _database_name
    
    cfg_path = os.path.join("config", "config.yaml")
    try:
        with open(cfg_path, "r") as f:
            config = yaml.safe_load(f)
        uri = config.get("mongo", {}).get("uri", "mongodb://localhost:27017")
        database = config.get("mongo", {}).get("database", "mg")
        # Connection pooling with optimized settings
        _mongo_client = MongoClient(
            uri,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000
        )
        _database_name = database
        return _mongo_client, _database_name
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")

@lru_cache(maxsize=1)
def get_available_stocks():
    """
    Get list of all available stock symbols from MongoDB collections.
    Cached to avoid repeated database queries.
    
    Returns:
        List of stock symbols (collection names ending with 'EQ')
    """
    try:
        client, db_name = get_mongo_client()
        db = client[db_name]
        
        # Get all collection names that end with 'EQ'
        collections = db.list_collection_names()
        stock_symbols = [col for col in collections if col.endswith('EQ')]
        
        # Sort alphabetically
        stock_symbols.sort()
        
        return stock_symbols
        
    except Exception as e:
        print(f"Error fetching stock list: {e}")
        return []

def milliseconds_to_ist(milliseconds):
    """
    Convert milliseconds timestamp to IST datetime.
    
    Args:
        milliseconds: Timestamp in milliseconds
    
    Returns:
        datetime object in IST timezone
    """
    # Convert milliseconds to seconds
    timestamp_seconds = milliseconds / 1000.0
    
    # Create UTC datetime
    utc_dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
    
    # Convert to IST (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_dt = utc_dt + ist_offset
    
    return ist_dt

# Data cache
_data_cache = {}
_cache_max_size = 100  # Maximum number of cached datasets

def _get_cache_key(symbol, start_date, end_date):
    """Generate a unique cache key for stock data."""
    key_str = f"{symbol}_{start_date}_{end_date}"
    return hashlib.md5(key_str.encode()).hexdigest()

def get_stock_data(symbol, start_date=None, end_date=None, use_cache=True):
    """
    Fetch historical stock data from MongoDB with caching.
    
    Args:
        symbol: Stock ticker symbol (collection name, e.g., 'BSECM:AADHARHFCEQ')
        start_date: Start date for data (YYYY-MM-DD) - optional
        end_date: End date for data (YYYY-MM-DD) - optional
        use_cache: Whether to use cached data (default: True)
    
    Returns:
        pandas DataFrame with columns: date, open, high, low, close, volume
    """
    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(symbol, start_date, end_date)
        if cache_key in _data_cache:
            return _data_cache[cache_key].copy()
    
    try:
        client, db_name = get_mongo_client()
        db = client[db_name]
        collection = db[symbol]
        
        # Build query
        query = {}
        
        if start_date or end_date:
            query["_id"] = {}
            if start_date:
                # Convert start_date to milliseconds
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                start_ms = int(start_dt.timestamp() * 1000)
                query["_id"]["$gte"] = start_ms
            if end_date:
                # Convert end_date to milliseconds
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_ms = int(end_dt.timestamp() * 1000)
                query["_id"]["$lte"] = end_ms
        
        # Query MongoDB with projection to fetch only required fields and batch size for memory efficiency
        projection = {'_id': 1, 'o': 1, 'h': 1, 'l': 1, 'c': 1, 'v': 1}
        cursor = collection.find(query, projection).sort("_id", 1).batch_size(1000)
        data = list(cursor)
        
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame using vectorized operations
        df = pd.DataFrame(data)
        
        # Vectorized datetime conversion
        df['date'] = pd.to_datetime(df['_id'], unit='ms', utc=True) + pd.Timedelta(hours=5, minutes=30)
        
        # Rename columns to standard format
        column_mapping = {
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
        
        # Select only required columns and convert to numeric types for faster processing
        df = df[required_cols].copy()
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Cache the result
        if use_cache:
            cache_key = _get_cache_key(symbol, start_date, end_date)
            if len(_data_cache) >= _cache_max_size:
                # Remove oldest entry (simple FIFO)
                _data_cache.pop(next(iter(_data_cache)))
            _data_cache[cache_key] = df.copy()
        
        return df
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()
