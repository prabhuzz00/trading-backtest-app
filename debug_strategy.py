"""
Debug script to check why no trades are triggering
"""
import sys
sys.path.insert(0, r'd:\project\trading-backtest-app\src')

from utils.db_connection import get_stock_data
import pandas as pd

# Check NIFTY1 data
print("Checking NSEFO:NIFTY1 data...")
data = get_stock_data("NSEFO:NIFTY1", "2023-01-01", "2023-12-31")

if data.empty:
    print("ERROR: No data found!")
else:
    print(f"\nTotal rows: {len(data)}")
    print(f"\nFirst 5 rows:")
    print(data.head())
    print(f"\nDate range: {data['date'].min()} to {data['date'].max()}")
    print(f"\nPrice range: {data['close'].min():.2f} to {data['close'].max():.2f}")
    print(f"\nChecking for zeros: {(data['close'] == 0).sum()} zero prices")
    
    # Check data frequency
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date')
    time_diffs = data['date'].diff()
    print(f"\nData frequency (most common time diff): {time_diffs.mode().values[0] if len(time_diffs.mode()) > 0 else 'Unknown'}")
    
    # Check weekdays
    data['weekday'] = data['date'].dt.dayofweek
    print(f"\nMondays in data: {(data['weekday'] == 0).sum()}")
    print(f"\nSample Mondays:")
    mondays = data[data['weekday'] == 0].head(10)
    for idx, row in mondays.iterrows():
        print(f"  {row['date']} - Close: {row['close']:.2f}")
