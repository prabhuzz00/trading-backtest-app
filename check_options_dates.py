"""
Check date ranges of options data
"""
import sys
sys.path.insert(0, 'src')

from utils.db_connection import get_mongo_client
from datetime import datetime

client, db_name = get_mongo_client()
db = client[db_name]

print("Checking NIFTY options date ranges...")
print("="*80)

collections = db.list_collection_names()
nifty_options = [c for c in collections if c.startswith('NSEFO:#NIFTY') and ('CE' in c or 'PE' in c)]

print(f"Found {len(nifty_options)} NIFTY options collections\n")

# Group by expiry date
expiry_dates = {}
for col in nifty_options:
    # Extract expiry from name: NSEFO:#NIFTY20241231CE24000
    try:
        parts = col.split('NIFTY')[1]
        expiry_str = parts[:8]  # YYYYMMDD
        expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
        
        if expiry_date not in expiry_dates:
            expiry_dates[expiry_date] = []
        expiry_dates[expiry_date].append(col)
    except:
        pass

print(f"Unique expiry dates: {len(expiry_dates)}\n")

# Show expiries by year
from collections import defaultdict
by_year = defaultdict(list)
for exp_date in sorted(expiry_dates.keys()):
    by_year[exp_date.year].append(exp_date)

for year in sorted(by_year.keys()):
    dates = by_year[year]
    print(f"\n{year}: {len(dates)} expiries")
    print(f"  Range: {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}")
    
    # Sample a few collections from this year
    sample_expiry = dates[len(dates)//2]  # Middle one
    sample_cols = expiry_dates[sample_expiry][:3]
    
    print(f"\n  Sample expiry: {sample_expiry.strftime('%Y-%m-%d')} ({len(expiry_dates[sample_expiry])} strikes)")
    for col in sample_cols:
        # Get date range of data in this collection
        first = db[col].find_one({}, sort=[('_id', 1)])
        last = db[col].find_one({}, sort=[('_id', -1)])
        
        if first and last:
            first_date = datetime.fromtimestamp(first['_id']/1000)
            last_date = datetime.fromtimestamp(last['_id']/1000)
            count = db[col].count_documents({})
            
            print(f"    {col:50s}")
            print(f"      Data: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')} ({count:,} docs)")

print("\n" + "="*80)
print("\nRECOMMENDATION:")
print("Use spot data (NSECM:NIFTY 50) from years where options data exists")
print("The strategies will fetch option premiums from the corresponding expiry dates")
