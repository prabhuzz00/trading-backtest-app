"""
Simple console test for options strategies
"""
import sys
sys.path.insert(0, 'src')

from strategies.short_vol_inventory import Strategy as ShortVolStrategy
from strategies.risk_defined_premium_band import Strategy as RiskBandStrategy
from utils.db_connection import get_stock_data

print("="*80)
print("SIMPLE OPTIONS STRATEGY TEST")
print("="*80)

# Get data
print("\n1. Fetching NIFTY 50 data...")
symbol = 'NSECM:NIFTY 50'
data = get_stock_data(symbol, '2024-01-01', '2024-12-31', use_cache=False)

if data is None or len(data) == 0:
    print("ERROR: No data found!")
    sys.exit(1)

print(f"OK - Got {len(data)} records from {data.date.iloc[0]} to {data.date.iloc[-1]}")

# Rename columns to lowercase (strategies expect lowercase)
data = data.rename(columns={
    'open': 'open',
    'high': 'high',
    'low': 'low',
    'close': 'close',
    'volume': 'volume',
    'date': 'date'
})

# Convert from paise to rupees (divide by 100)
print("\nConverting prices from paise to rupees...")
for col in ['open', 'high', 'low', 'close']:
    data[col] = data[col] / 100

# Keep date as a column (strategies need it)
# Don't set as index yet
print(f"Columns: {list(data.columns)}")
print(f"Price range: {data.close.min():.2f} to {data.close.max():.2f} (in Rupees)")
print(f"Sample prices: {data.close.iloc[-5:].tolist()}")

# Test Strategy 1: Short Vol Inventory
print("\n" + "="*80)
print("2. Testing Short Vol Inventory Strategy")
print("="*80)

try:
    strategy1 = ShortVolStrategy(
        num_strikes=2,
        strike_spacing_pct=0.02,
        profit_target_pct=0.5,
        stop_loss_pct=2.0,
        hold_days=5,
        strike_step=50  # 50 Rupees (not paise, since we converted data)
    )
    strategy1.set_underlying_symbol(symbol)
    
    print("Strategy initialized OK")
    print(f"Position before: {strategy1.position}")
    print(f"Legs before: {len(strategy1.options_legs) if strategy1.options_legs else 0}")
    
    # Call on_data with full dataset
    print("\nCalling on_data()...")
    
    # Add some debug output
    print(f"Data shape: {data.shape}")
    print(f"Data columns: {list(data.columns)}")
    print(f"Last bar: {data.iloc[-1].to_dict()}")
    
    result = strategy1.on_data(data)
    
    print(f"Result: {result}")
    print(f"Position after: {strategy1.position}")
    print(f"Legs after: {len(strategy1.options_legs) if strategy1.options_legs else 0}")
    
    # Check trade log
    trade_log = strategy1.get_trade_log()
    print(f"\nTrade Log: {len(trade_log)} entries")
    
    if len(trade_log) > 0:
        print("\nFIRST TRADE:")
        for key, value in trade_log[0].items():
            if key != 'legs':
                print(f"  {key}: {value}")
        if 'legs' in trade_log[0]:
            print(f"  legs: {len(trade_log[0]['legs'])} legs")
            for i, leg in enumerate(trade_log[0]['legs'][:3]):  # Show first 3 legs
                print(f"    Leg {i+1}: {leg.get('type')} Strike {leg.get('strike', 0)/100:.2f} Premium {leg.get('premium', 0)/100:.2f}")
                
        if len(trade_log) > 1:
            print(f"\nLAST TRADE:")
            for key, value in trade_log[-1].items():
                if key != 'legs':
                    print(f"  {key}: {value}")
    else:
        print("** NO TRADES TAKEN **")
        print("\nPossible reasons:")
        print("1. Entry conditions not met")
        print("2. Not enough data/history")
        print("3. Options premium calculation failed")
        print("4. Entry day filter (entry_day parameter)")
        
        # Debug info
        print(f"\nStrategy details:")
        print(f"  entry_day: {strategy1.entry_day}")
        print(f"  hold_days: {strategy1.hold_days}")
        print(f"  num_strikes: {strategy1.num_strikes}")
        print(f"  min_days_to_expiry: {strategy1.min_days_to_expiry}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test Strategy 2: Risk Band
print("\n" + "="*80)
print("3. Testing Risk Defined Premium Band Strategy")
print("="*80)

try:
    strategy2 = RiskBandStrategy(
        band_width_pct=0.05,
        spread_width_pct=0.03,
        profit_target_pct=0.7,
        stop_loss_pct=2.0,
        hold_days=5
    )
    strategy2.set_underlying_symbol(symbol)
    
    print("Strategy initialized OK")
    
    # Call on_data
    print("\nCalling on_data()...")
    result = strategy2.on_data(data)
    
    print(f"Result: {result}")
    print(f"Position: {strategy2.position}")
    
    # Check trade log
    trade_log = strategy2.get_trade_log()
    print(f"\nTrade Log: {len(trade_log)} entries")
    
    if len(trade_log) > 0:
        print(f"\nSUCCESS - {len(trade_log)} trades executed!")
        print(f"First trade action: {trade_log[0].get('action')}")
        print(f"Last trade action: {trade_log[-1].get('action')}")
    else:
        print("** NO TRADES TAKEN **")
        print(f"Entry day filter: {strategy2.entry_day}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
