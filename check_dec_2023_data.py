"""
Check what dates actually have data in the Dec 2023 expiry
"""
import sys
sys.path.append('src')

from utils.db_connection import get_stock_data
import pandas as pd

def check_dec_2023_option():
    """Check what data exists for Dec 2023 expiry"""
    
    print("\n" + "="*80)
    print("Checking Dec 2023 Expiry Option Data")
    print("="*80)
    
    # Try to get data for 18000 CE expiring Dec 28, 2023
    symbol = "NSEFO:#NIFTY20231228CE1800000"
    
    print(f"\nSymbol: {symbol}")
    print(f"Strike: ₹18,000 CE")
    print(f"Expiry: Dec 28, 2023")
    
    # Try to get full year data
    print("\nFetching data for full year 2023...")
    df = get_stock_data(symbol, "2023-01-01", "2023-12-31", use_cache=False)
    
    if df is None or df.empty:
        print("  ✗ No data found for 2023!")
    else:
        print(f"  ✓ Found {len(df)} records")
        
        # Convert from paise to rupees
        df['close'] = df['close'] / 100.0
        
        # Show date range
        print(f"\n  Date range:")
        print(f"    First: {df.iloc[0]['date']}")
        print(f"    Last: {df.iloc[-1]['date']}")
        
        # Show records by month
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly = df.groupby('month').size()
        
        print(f"\n  Records by month:")
        for month, count in monthly.items():
            print(f"    {month}: {count:,} records")
        
        # Show sample of first and last records
        print(f"\n  First 5 records:")
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            print(f"    {row['date']}: Close=₹{row['close']:,.2f}, Volume={row['volume']:,}")
        
        print(f"\n  Last 5 records:")
        for i in range(max(0, len(df)-5), len(df)):
            row = df.iloc[i]
            print(f"    {row['date']}: Close=₹{row['close']:,.2f}, Volume={row['volume']:,}")
        
        # Check for data in January
        jan_df = df[pd.to_datetime(df['date']).dt.month == 1]
        if not jan_df.empty:
            print(f"\n  ✓ Found {len(jan_df)} records in January 2023")
            print(f"    Sample (first 10):")
            for i in range(min(10, len(jan_df))):
                row = jan_df.iloc[i]
                print(f"      {row['date']}: Close=₹{row['close']:,.2f}")
        else:
            print(f"\n  ✗ No records in January 2023")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    check_dec_2023_option()
