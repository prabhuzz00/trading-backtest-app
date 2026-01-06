"""
Console test script to debug options strategies not taking trades
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.short_vol_inventory import Strategy as ShortVolInventoryStrategy
from strategies.short_put_ladder import Strategy as ShortPutLadderStrategy
from strategies.tail_wing_hedge import Strategy as TailWingHedgeStrategy
from strategies.risk_defined_premium_band import Strategy as RiskDefinedPremiumBandStrategy
from strategies.bullish_risk_reversal import Strategy as BullishRiskReversalStrategy
from strategies.bullish_carry_call_backspread import Strategy as BullishCarryCallBackspreadStrategy

from src.engine.options_backtest_engine import OptionsBacktestEngine
from utils.db_connection import get_stock_data

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_section(text):
    print(f"\n--- {text} ---")

def test_data_availability():
    """Test if we can fetch data from database"""
    print_header("TESTING DATA AVAILABILITY")
    
    try:
        # Test date range - use string format
        start_date = '2024-01-01'
        end_date = '2024-12-31'
        
        print_section("Fetching Nifty 50 data")
        symbol = 'NSECM:NIFTY 50'  # Correct MongoDB collection name
        print(f"Symbol: {symbol}")
        print(f"Date Range: {start_date} to {end_date}")
        
        data = get_stock_data(symbol, start_date, end_date, use_cache=False)
        
        if data is None or len(data) == 0:
            print("❌ NO DATA FOUND!")
            print("\nData is still not available. Check if MongoDB is running.")
        
        if data is not None and len(data) > 0:
            print(f"✅ Data fetched successfully!")
            print(f"   Records: {len(data)}")
            if hasattr(data, 'index'):
                print(f"   Date Range: {data.index[0] if hasattr(data.index[0], 'date') else data['date'].iloc[0]} to {data.index[-1] if hasattr(data.index[-1], 'date') else data['date'].iloc[-1]}")
            print(f"   Columns: {list(data.columns)}")
            print(f"\nFirst few rows:")
            print(data.head())
            print(f"\nLast few rows:")
            print(data.tail())
            return True, data
        else:
            print("❌ FAILED to fetch data!")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def test_strategy_initialization(strategy_class, strategy_name, params):
    """Test if strategy can be initialized"""
    print_header(f"TESTING {strategy_name} INITIALIZATION")
    
    try:
        # Initialize strategy
        strategy = strategy_class(**params)
        strategy.set_underlying_symbol('NSECM:NIFTY 50')  # Use correct symbol
        
        print(f"✅ Strategy initialized successfully")
        print(f"   Class: {strategy.__class__.__name__}")
        print(f"   Parameters: {params}")
        print(f"   Position: {strategy.position}")
        print(f"   Options Legs: {strategy.options_legs}")
        
        return True, strategy
    except Exception as e:
        print(f"❌ ERROR initializing strategy: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def test_strategy_on_data(strategy, data, strategy_name):
    """Test strategy with actual data"""
    print_header(f"TESTING {strategy_name} WITH REAL DATA")
    
    if data is None or len(data) == 0:
        print("❌ No data available for testing")
        return
    
    # Ensure required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    
    # Check if columns are lowercase or uppercase
    cols_lower = [c.lower() for c in data.columns]
    if all(col in cols_lower for col in required_cols):
        # Rename to match case
        col_mapping = {c: c.capitalize() for c in data.columns if c.lower() in required_cols}
        data = data.rename(columns=col_mapping)
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    for col in required_cols:
        if col not in data.columns:
            print(f"❌ Missing required column: {col}")
            return
    
    print_section("Data Preprocessing")
    # Make sure we have proper OHLCV data
    data = data[required_cols].copy()
    data = data.dropna()
    print(f"Clean data rows: {len(data)}")
    
    if len(data) == 0:
        print("❌ No valid data after cleaning")
        return
    
    print_section("Strategy Execution Simulation")
    
    trades_taken = 0
    positions_entered = 0
    positions_exited = 0
    
    # Start from row 20 to ensure we have enough history
    start_idx = max(20, len(data) // 4)  # Start from 25% into dataset
    end_idx = min(start_idx + 100, len(data))  # Test 100 bars
    
    print(f"Testing from index {start_idx} to {end_idx} ({end_idx - start_idx} bars)")
    print(f"Date range: {data.index[start_idx]} to {data.index[end_idx-1]}")
    
    for i in range(start_idx, end_idx):
        current_bar = data.iloc[i]
        historical_data = data.iloc[:i+1]
        
        # Check position before
        position_before = strategy.position
        legs_before = len(strategy.options_legs) if strategy.options_legs else 0
        
        # Call strategy
        try:
            result = strategy.on_data(current_bar, historical_data)
            
            # Check position after
            position_after = strategy.position
            legs_after = len(strategy.options_legs) if strategy.options_legs else 0
            
            # Detect position changes
            if position_before is None and position_after is not None:
                positions_entered += 1
                print(f"\n📊 POSITION ENTERED at {current_bar.name}")
                print(f"   Spot: {current_bar['Close']:.2f}")
                print(f"   Position: {position_after}")
                print(f"   Legs: {legs_after}")
                if strategy.options_legs:
                    for leg in strategy.options_legs:
                        print(f"   - {leg.get('type')}: Strike {leg.get('strike')} @ ₹{leg.get('premium'):.2f}")
            
            elif position_before is not None and position_after is None:
                positions_exited += 1
                print(f"\n📊 POSITION EXITED at {current_bar.name}")
                print(f"   Spot: {current_bar['Close']:.2f}")
                
            # Show progress every 20 bars
            if i % 20 == 0:
                print(f"   Bar {i - start_idx + 1}/{end_idx - start_idx}: {current_bar.name.date()} | Spot: {current_bar['Close']:.2f} | Position: {strategy.position}")
                
        except Exception as e:
            print(f"\n❌ ERROR at bar {i} ({current_bar.name}): {str(e)}")
            import traceback
            traceback.print_exc()
            break
    
    print_section("Results")
    print(f"Bars tested: {end_idx - start_idx}")
    print(f"Positions entered: {positions_entered}")
    print(f"Positions exited: {positions_exited}")
    
    # Check trade log
    trade_log = strategy.get_trade_log()
    print(f"\nTrade Log Entries: {len(trade_log)}")
    
    if len(trade_log) > 0:
        print("\nTrade Log:")
        for idx, trade in enumerate(trade_log, 1):
            print(f"\n  Trade {idx}:")
            print(f"    Date: {trade.get('date')}")
            print(f"    Action: {trade.get('action')}")
            print(f"    Spot: {trade.get('spot', 0):.2f}")
            print(f"    P&L: {trade.get('pnl', 0):.2f}")
            if 'legs' in trade:
                print(f"    Legs: {len(trade['legs'])}")
                for leg in trade['legs']:
                    print(f"      - {leg.get('type')}: Strike {leg.get('strike')} @ ₹{leg.get('premium'):.2f}")
    else:
        print("\n⚠️ NO TRADES IN LOG - Strategy did not enter any positions!")
        print("\nDEBUGGING INFO:")
        print(f"  Strategy has generate_signal method: {hasattr(strategy, 'generate_signal')}")
        print(f"  Strategy has on_data method: {hasattr(strategy, 'on_data')}")
        print(f"  Current position: {strategy.position}")
        print(f"  Options legs: {strategy.options_legs}")
        
        # Check entry conditions
        print("\nChecking entry conditions on a sample bar...")
        sample_bar = data.iloc[start_idx + 10]
        sample_hist = data.iloc[:start_idx + 11]
        
        print(f"  Sample Date: {sample_bar.name}")
        print(f"  Spot Price: {sample_bar['Close']:.2f}")
        print(f"  Historical data: {len(sample_hist)} bars")
        
        # Try to understand why no entry
        if hasattr(strategy, 'min_holding_period'):
            print(f"  Min holding period: {strategy.min_holding_period}")
        if hasattr(strategy, 'profit_target_pct'):
            print(f"  Profit target: {strategy.profit_target_pct * 100:.1f}%")
        if hasattr(strategy, 'stop_loss_pct'):
            print(f"  Stop loss: {strategy.stop_loss_pct * 100:.1f}%")

def test_with_backtest_engine(strategy_class, strategy_name, params, data):
    """Test strategy with actual backtest engine"""
    print_header(f"TESTING {strategy_name} WITH BACKTEST ENGINE")
    
    if data is None or len(data) == 0:
        print("❌ No data available")
        return
    
    try:
        # Initialize strategy
        strategy = strategy_class(**params)
        strategy.set_underlying_symbol('NSECM:NIFTY 50')  # Use correct symbol
        
        # Create engine
        engine = OptionsBacktestEngine(
            strategy=strategy,
            data=data,
            initial_capital=100000,
            brokerage_pct=0.0001
        )
        
        print(f"✅ Engine initialized")
        print(f"   Initial Capital: ₹{engine.initial_capital:,.0f}")
        print(f"   Data Points: {len(data)}")
        
        # Run backtest
        print("\nRunning backtest...")
        results = engine.run()
        
        print_section("Backtest Results")
        
        if results is None:
            print("❌ No results returned")
            return
        
        # Print summary
        print(f"Total Return: {results.get('total_return', 0):.2f}%")
        print(f"Total Trades: {results.get('total_trades', 0)}")
        print(f"Winning Trades: {results.get('winning_trades', 0)}")
        print(f"Losing Trades: {results.get('losing_trades', 0)}")
        print(f"Win Rate: {results.get('win_rate', 0):.2f}%")
        print(f"Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
        
        if results.get('total_trades', 0) == 0:
            print("\n⚠️ WARNING: No trades executed!")
            
            # Debug info
            print("\nEngine Debug Info:")
            print(f"  Strategy position: {strategy.position}")
            print(f"  Trade log length: {len(strategy.get_trade_log())}")
            print(f"  Equity curve length: {len(results.get('equity_curve', []))}")
        else:
            print("\n✅ Trades executed successfully!")
            
            # Show trade details
            trades_df = results.get('trades', pd.DataFrame())
            if not trades_df.empty:
                print(f"\nTrade Details:")
                print(trades_df.to_string())
                
    except Exception as e:
        print(f"❌ ERROR in backtest: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print_header("OPTIONS STRATEGY DEBUG TEST")
    print(f"Date: {datetime.now()}")
    
    # Test data availability first
    data_ok, data = test_data_availability()
    
    if not data_ok:
        print("\n" + "="*80)
        print("❌ CANNOT PROCEED - No data available!")
        print("="*80)
        print("\nPossible issues:")
        print("1. MongoDB is not running")
        print("2. Database name is incorrect")
        print("3. Symbol name is incorrect ('NIFTY 50' vs 'NIFTY' vs '^NSEI')")
        print("4. No data exists in the date range")
        print("\nPlease check your database and try again.")
        return
    
    # Define strategies to test
    strategies_to_test = [
        {
            'class': ShortVolInventoryStrategy,
            'name': 'Short Vol Inventory',
            'params': {
                'num_strikes': 2,
                'strike_spacing_pct': 0.02,
                'profit_target_pct': 0.5,
                'stop_loss_pct': 2.0,
                'hold_days': 5
            }
        },
        {
            'class': RiskDefinedPremiumBandStrategy,
            'name': 'Risk Defined Premium Band',
            'params': {
                'band_width_pct': 0.05,
                'spread_width_pct': 0.03,
                'profit_target_pct': 0.7,
                'stop_loss_pct': 2.0,
                'hold_days': 5
            }
        },
        {
            'class': BullishRiskReversalStrategy,
            'name': 'Bullish Risk Reversal',
            'params': {
                'call_strike_otm_pct': 0.03,
                'put_strike_otm_pct': 0.03,
                'momentum_threshold': 0.01,
                'profit_target_pct': 1.0,
                'stop_loss_pct': 2.0,
                'hold_days': 5
            }
        }
    ]
    
    # Test each strategy
    for strategy_info in strategies_to_test:
        # Test initialization
        init_ok, strategy = test_strategy_initialization(
            strategy_info['class'],
            strategy_info['name'],
            strategy_info['params']
        )
        
        if not init_ok:
            continue
        
        # Test with data
        test_strategy_on_data(strategy, data, strategy_info['name'])
        
        # Test with backtest engine
        test_with_backtest_engine(
            strategy_info['class'],
            strategy_info['name'],
            strategy_info['params'],
            data
        )
        
        print("\n" + "-"*80 + "\n")
    
    print_header("TEST COMPLETE")
    print("\nIf no trades were taken, check:")
    print("1. Entry conditions might be too strict")
    print("2. Not enough historical data for indicators")
    print("3. Options premium calculation returning None")
    print("4. Strategy logic has bugs")
    print("\nReview the debug output above to identify the issue.")

if __name__ == '__main__':
    main()
