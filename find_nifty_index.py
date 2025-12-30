"""
Find the NIFTY index or underlying symbol
"""

import sys
sys.path.insert(0, r'd:\project\trading-backtest-app\src')

from utils.db_connection import get_mongo_client

try:
    client, db_name = get_mongo_client()
    db = client[db_name]
    
    # Get all collections
    collections = db.list_collection_names()
    
    # Search for NIFTY index
    print("="*80)
    print("Searching for NIFTY index/underlying data...")
    print("="*80)
    
    # Look for NIFTY index collections (not options)
    nifty_index = [c for c in collections if 'NIFTY' in c and 'CE' not in c and 'PE' not in c]
    
    if nifty_index:
        print(f"\nFound {len(nifty_index)} NIFTY index/future collections:")
        for i, col in enumerate(nifty_index):
            print(f"  {i+1}. {col}")
            
            # Sample data from first collection
            if i == 0:
                sample = db[col].find_one()
                if sample:
                    print(f"\n     Sample data structure:")
                    for key, value in sample.items():
                        print(f"       {key}: {value}")
    else:
        print("\nNo NIFTY index data found.")
        print("\nSearching for any NIFTY collections...")
        nifty_all = [c for c in collections if 'NIFTY' in c.upper()][:20]
        for col in nifty_all:
            print(f"  - {col}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
