"""
Debug why no trades are generated
"""
import sys
sys.path.append('src')

from strategies.risk_defined_premium_band import Strategy as RiskDefinedPremiumBand
from utils.db_connection import get_stock_data
from engine.options_backtest_engine import OptionsBacktestEngine
import pandas as pd

def debug_strategy():
    """Debug the strategy to see why no trades are generated"""
    
    print("\n" + "="*80)
    print("Debugging Risk-Defined Premium Band Strategy")
    print("="*80)
    
    # Get NIFTY data for 2023
    print("\n1. Fetching NIFTY data...")
    data = get_stock_data("NSECM:NIFTY 50", "2023-01-01", "2023-03-31", use_cache=True)
    
    if data is None or data.empty:
        print("  ✗ No data found!")
        return
    
    # Convert from paise to Rupees
    data['open'] = data['open'] / 100.0
    data['high'] = data['high'] / 100.0
    data['low'] = data['low'] / 100.0
    data['close'] = data['close'] / 100.0
    
    print(f"  ✓ Loaded {len(data)} bars")
    print(f"  First date: {data.iloc[0]['date']}")
    print(f"  Last date: {data.iloc[-1]['date']}")
    print(f"  First close: ₹{data.iloc[0]['close']:,.2f}")
    
    # Create strategy
    print("\n2. Initializing strategy...")
    strategy = RiskDefinedPremiumBand()
    print(f"  Strike step: {strategy.strike_step}")
    
    # Adjust strike_step
    if strategy.strike_step >= 1000:
        strategy.strike_step = strategy.strike_step / 100.0
        print(f"  Adjusted strike_step: {strategy.strike_step}")
    
    # Setup engine access
    print("\n3. Setting up engine access...")
    engine = OptionsBacktestEngine()
    engine._get_available_expiries()
    
    # Inject engine methods
    strategy._engine_get_closest_expiry = engine._get_closest_expiry
    strategy._engine_get_available_strikes = engine._get_available_strikes
    strategy._engine_find_atm_strike = engine._find_atm_strike
    strategy._engine_find_otm_call_strike = engine._find_otm_call_strike
    strategy._engine_find_otm_put_strike = engine._find_otm_put_strike
    strategy._engine_find_itm_call_strike = engine._find_itm_call_strike
    strategy._engine_find_itm_put_strike = engine._find_itm_put_strike
    strategy._engine_fetch_option_premium = engine._fetch_option_premium
    
    print("  ✓ Engine methods injected")
    
    # Call strategy
    print("\n4. Calling strategy.on_data()...")
    strategy.on_data(data)
    
    print("\n5. Getting trade log...")
    trades = strategy.get_trade_log()
    print(f"  Number of trades: {len(trades)}")
    
    if len(trades) == 0:
        print("\n  Investigating why no trades...")
        
        # Check first few bars
        print("\n  Checking first 35 bars (need 30 for entry):")
        for i in range(min(35, len(data))):
            bar = data.iloc[i]
            print(f"    Bar {i+1}: {bar['date'].strftime('%Y-%m-%d')}, Close=₹{bar['close']:,.2f}")
        
        # Try manually checking entry conditions
        print("\n  Checking entry conditions at bar 31:")
        if len(data) >= 31:
            current_bar = data.iloc[30]
            historical_data = data.iloc[:31]
            
            print(f"    Current bar: {current_bar['date'].strftime('%Y-%m-%d')}")
            print(f"    Spot: ₹{current_bar['close']:,.2f}")
            print(f"    Position: {strategy.position}")
            print(f"    Historical bars: {len(historical_data)}")
            
            should_enter = strategy.should_enter(historical_data)
            print(f"    Should enter: {should_enter}")
            
            if should_enter:
                print("\n  Attempting to build premium band...")
                band = strategy.build_premium_band(current_bar, historical_data)
                if band:
                    print(f"    ✓ Band created successfully!")
                    print(f"    Legs: {len(band)}")
                else:
                    print(f"    ✗ Failed to build band")
    else:
        print(f"\n  ✓ Trades generated!")
        for i, trade in enumerate(trades[:3], 1):
            print(f"\n  Trade {i}:")
            print(f"    Date: {trade['date']}")
            print(f"    Action: {trade['action']}")
            print(f"    Spot: ₹{trade['spot']:,.2f}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    debug_strategy()
