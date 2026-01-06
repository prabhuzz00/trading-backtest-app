"""
Quick script to check what data is available in MongoDB
"""
from utils.db_connection import get_db_connection

# Connect to MongoDB
client, db = get_db_connection()

if db is not None:
    print("✅ Connected to MongoDB")
    
    # List all collections
    print("\n📊 Available Collections:")
    collections = db.list_collection_names()
    for coll in collections:
        print(f"  - {coll}")
    
    # Check stocks collection
    if 'stocks' in collections:
        stocks_coll = db['stocks']
        
        # Count documents
        count = stocks_coll.count_documents({})
        print(f"\n📈 stocks collection: {count} documents")
        
        # Get unique symbols
        symbols = stocks_coll.distinct('symbol')
        print(f"\n🎯 Unique symbols ({len(symbols)}):")
        for sym in sorted(symbols)[:20]:  # Show first 20
            print(f"  - {sym}")
        if len(symbols) > 20:
            print(f"  ... and {len(symbols) - 20} more")
        
        # Sample document
        sample = stocks_coll.find_one()
        if sample:
            print(f"\n📄 Sample document:")
            print(f"  Symbol: {sample.get('symbol')}")
            print(f"  Date: {sample.get('date')}")
            print(f"  Fields: {list(sample.keys())}")
            
        # Check for NIFTY variations
        print(f"\n🔍 Checking for NIFTY symbols:")
        nifty_symbols = stocks_coll.distinct('symbol', {'symbol': {'$regex': 'NIFTY', '$options': 'i'}})
        if nifty_symbols:
            for sym in nifty_symbols:
                doc_count = stocks_coll.count_documents({'symbol': sym})
                sample_doc = stocks_coll.find_one({'symbol': sym})
                date_range = ""
                if sample_doc:
                    first_date = stocks_coll.find_one({'symbol': sym}, sort=[('date', 1)])
                    last_date = stocks_coll.find_one({'symbol': sym}, sort=[('date', -1)])
                    if first_date and last_date:
                        date_range = f" ({first_date.get('date')} to {last_date.get('date')})"
                print(f"  - {sym}: {doc_count} records{date_range}")
        else:
            print("  ❌ No NIFTY symbols found!")
    else:
        print("\n❌ 'stocks' collection not found!")
        
else:
    print("❌ Could not connect to MongoDB")
