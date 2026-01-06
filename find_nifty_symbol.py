"""
Find correct symbol name for NIFTY in MongoDB
"""
import sys
sys.path.insert(0, 'src')

from utils.db_connection import get_mongo_client, get_available_stocks

print("Connecting to MongoDB...")
try:
    client, db_name = get_mongo_client()
    db = client[db_name]
    
    print(f"✅ Connected to database: {db_name}")
    
    # Get all collections
    collections = db.list_collection_names()
    print(f"\nTotal collections: {len(collections)}")
    
    # Find NIFTY-related collections
    print("\n🔍 Searching for NIFTY collections...")
    nifty_collections = [c for c in collections if 'NIFTY' in c.upper()]
    
    if nifty_collections:
        print(f"\n✅ Found {len(nifty_collections)} NIFTY-related collections:")
        for coll in sorted(nifty_collections)[:30]:  # Show first 30
            # Get document count
            count = db[coll].count_documents({})
            # Get date range
            first = db[coll].find_one({}, sort=[('_id', 1)])
            last = db[coll].find_one({}, sort=[('_id', -1)])
            
            date_range = ""
            if first and last:
                from datetime import datetime
                first_date = datetime.fromtimestamp(first['_id'] / 1000).strftime('%Y-%m-%d')
                last_date = datetime.fromtimestamp(last['_id'] / 1000).strftime('%Y-%m-%d')
                date_range = f" | {first_date} to {last_date}"
            
            print(f"  {coll:50s} | {count:6d} docs{date_range}")
            
        if len(nifty_collections) > 30:
            print(f"  ... and {len(nifty_collections) - 30} more")
            
    else:
        print("❌ No NIFTY collections found!")
        print("\nShowing first 20 collections:")
        for coll in sorted(collections)[:20]:
            count = db[coll].count_documents({})
            print(f"  {coll:50s} | {count:6d} docs")
    
    # Try to get available stocks
    print("\n\n📊 Getting available stocks via get_available_stocks()...")
    stocks = get_available_stocks()
    print(f"Found {len(stocks)} stocks")
    if stocks:
        nifty_stocks = [s for s in stocks if 'NIFTY' in s.upper()]
        if nifty_stocks:
            print(f"\nNIFTY stocks: {nifty_stocks}")
        else:
            print(f"Sample stocks: {stocks[:10]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
