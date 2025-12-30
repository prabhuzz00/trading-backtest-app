"""
Check data availability for NIFTY symbols
"""

import sys
sys.path.insert(0, r'd:\project\trading-backtest-app\src')

from utils.db_connection import get_stock_data
import pandas as pd

symbols_to_check = [
    "NSEFO:NIFTY1",
    "NSEFO:NIFTY2",
    "NSEFO:NIFTY3",
    "NSECM:NIFTY 50",
]

for symbol in symbols_to_check:
    print(f"\n{'='*80}")
    print(f"Checking: {symbol}")
    print(f"{'='*80}")
    
    # Get all data without date range
    data = get_stock_data(symbol, use_cache=False)
    
    if data.empty:
        print("  ❌ No data available")
    else:
        print(f"  ✅ Data available: {len(data)} rows")
        print(f"  Date Range: {data['date'].min()} to {data['date'].max()}")
        print(f"  Sample prices: {data['close'].head(3).values}")
        print(f"  Price range: {data['close'].min():.2f} to {data['close'].max():.2f}")
