"""
Test if options data exists in MongoDB
"""
import sys
sys.path.insert(0, 'src')

from utils.db_connection import get_mongo_client, get_stock_data
from datetime import datetime, timedelta

print("="*80)
print("CHECKING OPTIONS DATA IN MONGODB")
print("="*80)

client, db_name = get_mongo_client()
db = client[db_name]

# Search for NIFTY options collections
print("\n1. Searching for NIFTY options collections (NSEFO:#NIFTY...)...")
collections = db.list_collection_names()
nifty_options = [c for c in collections if c.startswith('NSEFO:#NIFTY') and ('CE' in c or 'PE' in c)]

print(f"Found {len(nifty_options)} NIFTY options collections")

if len(nifty_options) > 0:
    print("\nSample collections:")
    for col in sorted(nifty_options)[:10]:
        count = db[col].count_documents({})
        print(f"  {col:60s} | {count:6d} docs")
    
    # Test fetching data from one
    print("\n2. Testing data fetch from sample option...")
    test_col = nifty_options[0]
    print(f"Collection: {test_col}")
    
    # Get a sample document
    sample = db[test_col].find_one()
    if sample:
        print(f"Sample document:")
        print(f"  _id (timestamp): {sample.get('_id')}")
        print(f"  Date: {datetime.fromtimestamp(sample.get('_id', 0)/1000)}")
        print(f"  close: {sample.get('c', 0)/100:.2f} (in Rupees)")
        print(f"  Fields: {list(sample.keys())}")
    
    # Test get_stock_data
    print(f"\n3. Testing get_stock_data function...")
    data = get_stock_data(test_col, '2024-11-01', '2024-11-30', use_cache=False)
    if data is not None and len(data) > 0:
        print(f"SUCCESS - Got {len(data)} records")
        print(f"Date range: {data.date.iloc[0]} to {data.date.iloc[-1]}")
        print(f"Price range: {data.close.min()/100:.2f} to {data.close.max()/100:.2f} Rupees")
    else:
        print("FAILED - No data returned")
        
else:
    print("\n❌ NO NIFTY OPTIONS DATA FOUND!")
    print("\nOptions data should be in format:")
    print("  NSEFO:#NIFTY20241231CE24000")
    print("  NSEFO:#NIFTY20241231PE23000")
    print("  etc.")
    
    # Check what NSEFO collections exist
    print("\n\nChecking all NSEFO collections...")
    nsefo_cols = [c for c in collections if c.startswith('NSEFO')]
    print(f"Found {len(nsefo_cols)} NSEFO collections")
    if len(nsefo_cols) > 0:
        print("\nSample NSEFO collections:")
        for col in sorted(nsefo_cols)[:20]:
            print(f"  {col}")

print("\n" + "="*80)
