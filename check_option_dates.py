"""
Check what actual data exists in an options collection
"""
import sys
sys.path.append('src')

from utils.db_connection import get_mongo_client
import pandas as pd
from datetime import datetime

def check_option_collection():
    """Check what data is in an actual option collection"""
    
    print("\n" + "="*80)
    print("Checking Option Collection Data")
    print("="*80)
    
    # Pick a specific option to examine
    symbol = "NSEFO:#NIFTY20231228CE1800000"  # 18000 CE expiring Dec 28, 2023
    
    print(f"\nCollection: {symbol}")
    print(f"Strike: ₹18,000")
    print(f"Type: Call")
    print(f"Expiry: Dec 28, 2023")
    
    try:
        client, db_name = get_mongo_client()
        db = client[db_name]
        collection = db[symbol]
        
        # Get total count
        count = collection.count_documents({})
        print(f"\nTotal documents: {count}")
        
        if count > 0:
            # Get first document to see full structure
            sample = collection.find_one()
            print(f"\nSample document:")
            for key, value in sample.items():
                if key != '_id':
                    print(f"  {key}: {value} (type: {type(value).__name__})")
            
            print("\n\nFirst 10 documents:")
            cursor = collection.find().limit(10)
            
            for i, doc in enumerate(cursor, 1):
                print(f"\nDocument {i}:")
                for key, value in doc.items():
                    if key != '_id':
                        if key == 'c':  # Close price
                            close_rupees = value / 100.0 if value else 0
                            print(f"  {key}: {value} (₹{close_rupees:,.2f})")
                        else:
                            print(f"  {key}: {value}")
        
        else:
            print("Collection is empty!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("Check Complete")
    print("="*80 + "\n")

if __name__ == "__main__":
    check_option_collection()
