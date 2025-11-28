import pandas as pd
from pymongo import MongoClient
import yaml
import os
from datetime import datetime, timezone, timedelta

def get_mongo_client():
    """Load MongoDB URI from config and return a client."""
    cfg_path = os.path.join("config", "config.yaml")
    try:
        with open(cfg_path, "r") as f:
            config = yaml.safe_load(f)
        uri = config.get("mongo", {}).get("uri", "mongodb://localhost:27017")
        database = config.get("mongo", {}).get("database", "mg")
        client = MongoClient(uri)
        return client, database
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")

def get_available_stocks():
    """
    Get list of all available stock symbols from MongoDB collections.
    
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

def get_stock_data(symbol, start_date=None, end_date=None):
    """
    Fetch historical stock data from MongoDB.
    
    Args:
        symbol: Stock ticker symbol (collection name, e.g., 'BSECM:AADHARHFCEQ')
        start_date: Start date for data (YYYY-MM-DD) - optional
        end_date: End date for data (YYYY-MM-DD) - optional
    
    Returns:
        pandas DataFrame with columns: date, open, high, low, close, volume
    """
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
        
        # Query MongoDB for the stock data
        cursor = collection.find(query).sort("_id", 1)
        data = list(cursor)
        
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert _id (milliseconds) to IST datetime
        df['date'] = df['_id'].apply(milliseconds_to_ist)
        
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
        
        # Select only required columns
        df = df[required_cols]
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()
