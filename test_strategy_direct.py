"""
Comprehensive debug to test strategy directly
"""
import sys
sys.path.insert(0, r'd:\project\trading-backtest-app\src')
sys.path.insert(0, r'd:\project\trading-backtest-app')

from utils.db_connection import get_stock_data
from engine.strategy_loader import load_strategy
import pandas as pd

print("="*80)
print("DIRECT STRATEGY TEST")
print("="*80)

# Load data
print("\n1. Loading data...")
data = get_stock_data("NSEFO:NIFTY1", "2023-01-02", "2023-01-03")
print(f"   Rows: {len(data)}")

# Load strategy
print("\n2. Loading strategy...")
strategy = load_strategy("strategies/bull_call_spread.py")
print(f"   Strategy loaded: {strategy.__class__.__name__}")
print(f"   Momentum threshold: {strategy.momentum_threshold}")
print(f"   Volatility threshold: {strategy.volatility_threshold}")

# Test first Monday
print("\n3. Testing strategy on first Monday bars...")
data['date'] = pd.to_datetime(data['date'])
data = data.sort_values('date')

signals_found = 0
for idx in range(100, min(200, len(data))):
    row = {
        'date': data.iloc[idx]['date'],
        'open': data.iloc[idx]['open'],
        'high': data.iloc[idx]['high'],
        'low': data.iloc[idx]['low'],
        'close': data.iloc[idx]['close'],
        'volume': data.iloc[idx]['volume']
    }
    
    hist_data = data.iloc[max(0, idx-500):idx+1]
    
    signal = strategy.generate_signal(row, hist_data)
    
    if signal != 'HOLD':
        print(f"\n   Bar {idx}: {row['date']}")
        print(f"   Signal: {signal}")
        print(f"   Price: {row['close']}")
        signals_found += 1
        
        if signals_found >= 3:
            break

if signals_found == 0:
    print("\n   No BUY/SELL signals found in first 100 bars")
    print("\n4. Checking what prevents entry...")
    
    # Check one specific bar
    idx = 150
    row = {
        'date': data.iloc[idx]['date'],
        'open': data.iloc[idx]['open'],
        'high': data.iloc[idx]['high'],
        'low': data.iloc[idx]['low'],
        'close': data.iloc[idx]['close'],
        'volume': data.iloc[idx]['volume']
    }
    hist_data = data.iloc[max(0, idx-500):idx+1]
    
    print(f"\n   Testing bar {idx}: {row['date']}")
    print(f"   Weekday: {row['date'].weekday()} (0=Monday)")
    print(f"   Close: {row['close']}")
    print(f"   Historical data length: {len(hist_data)}")
    
    # Manually check conditions
    closes = hist_data['close'].values
    if len(closes) >= 50:
        momentum = (closes[-1] - closes[-50]) / closes[-50]
        print(f"   Momentum (50 bars): {momentum:.6f} (need >= {strategy.momentum_threshold})")
        print(f"   Momentum OK: {momentum >= strategy.momentum_threshold}")
    
    signal = strategy.generate_signal(row, hist_data)
    print(f"   Signal returned: {signal}")

print("\n" + "="*80)
