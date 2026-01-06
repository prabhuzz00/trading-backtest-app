"""
Test fetching real premium directly
"""
import sys
sys.path.append('src')

from engine.options_backtest_engine import OptionsBacktestEngine
from datetime import datetime
import pandas as pd

def test_fetch_premium():
    """Test the premium fetching method"""
    
    print("\n" + "="*80)
    print("Testing Premium Fetch")
    print("="*80)
    
    engine = OptionsBacktestEngine()
    
    # Test with Jan 2, 2023
    strike = 18000.0
    option_type = 'CE'
    current_date = pd.Timestamp('2023-01-02 09:30:00', tz='UTC')
    expiry_date = datetime(2023, 12, 28)
    
    print(f"\nTest parameters:")
    print(f"  Strike: ₹{strike:,.0f}")
    print(f"  Type: {option_type}")
    print(f"  Current date: {current_date}")
    print(f"  Expiry date: {expiry_date}")
    
    print("\nCalling _fetch_option_premium...")
    premium = engine._fetch_option_premium(strike, option_type, current_date, expiry_date)
    
    if premium:
        print(f"  ✓ Premium: ₹{premium:,.2f}")
    else:
        print(f"  ✗ No premium returned")
        
        # Try manually
        print("\n  Trying manual query...")
        from utils.db_connection import get_stock_data
        
        strike_paise = int(strike * 100)
        expiry_str = expiry_date.strftime('%Y%m%d')
        symbol = f"NSEFO:#NIFTY{expiry_str}{option_type}{strike_paise}"
        
        print(f"  Symbol: {symbol}")
        
        current_date_obj = pd.to_datetime(current_date)
        if current_date_obj.tz is not None:
            current_date_obj = current_date_obj.tz_localize(None)
        
        from datetime import timedelta
        start_date = (current_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (current_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"  Date range: {start_date} to {end_date}")
        
        df = get_stock_data(symbol, start_date, end_date, use_cache=True)
        
        if df is None or df.empty:
            print(f"  ✗ No data returned from get_stock_data")
        else:
            print(f"  ✓ Got {len(df)} records")
            print(f"\n  Sample records:")
            for i in range(min(5, len(df))):
                row = df.iloc[i]
                close_rupees = row['close'] / 100.0
                print(f"    {row['date']}: Close=₹{close_rupees:,.2f}")
            
            # Find closest
            df['date_diff'] = abs((df['date'] - current_date_obj).dt.total_seconds())
            closest_idx = df['date_diff'].idxmin()
            premium_paise = df.loc[closest_idx, 'close']
            premium_rupees = premium_paise / 100.0
            
            print(f"\n  Closest record: {df.loc[closest_idx, 'date']}")
            print(f"  Premium: ₹{premium_rupees:,.2f}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_fetch_premium()
