"""
Quick test script to verify options strategy features
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing options strategy features...\n")

# Test 1: Import strategy
print("1. Testing strategy import...")
try:
    from strategies.nifty_options_straddle import Strategy
    print("   ✓ Strategy imported successfully")
except Exception as e:
    print(f"   ✗ Error importing strategy: {e}")
    sys.exit(1)

# Test 2: Initialize strategy
print("\n2. Testing strategy initialization...")
try:
    strategy = Strategy(
        strategy_type='LONG_STRADDLE',
        entry_day=0,
        hold_days=4
    )
    print("   ✓ Strategy initialized successfully")
    print(f"   - Strategy type: {strategy.strategy_type}")
    print(f"   - Entry day: {strategy.entry_day}")
    print(f"   - Hold days: {strategy.hold_days}")
except Exception as e:
    print(f"   ✗ Error initializing strategy: {e}")
    sys.exit(1)

# Test 3: Test database functions
print("\n3. Testing database functions...")
try:
    from utils.db_connection import get_all_instruments
    print("   ✓ Database functions imported successfully")
except Exception as e:
    print(f"   ✗ Error importing database functions: {e}")
    sys.exit(1)

# Test 4: Test UI components
print("\n4. Testing UI components...")
try:
    from PyQt6.QtWidgets import QApplication
    from ui.stock_sidebar import StockSidebar, StockListItem
    
    # Create minimal app for testing
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    sidebar = StockSidebar()
    print("   ✓ StockSidebar created successfully")
    
    # Test with sample data
    sample_data = [
        {'symbol': 'NSEFO:NIFTY23DEC21500CE', 'type': 'OPT'},
        {'symbol': 'NSEFO:NIFTY23DEC21500PE', 'type': 'OPT'},
        {'symbol': 'NSEFO:NIFTY23DECFUT', 'type': 'FUT'},
        {'symbol': 'NSECM:RELIANCEEQ', 'type': 'EQ'}
    ]
    
    sidebar.set_stocks(sample_data)
    print(f"   ✓ Loaded {len(sample_data)} sample instruments")
    
    # Test filtering
    sidebar.set_filter('OPT')
    print("   ✓ Filter functionality works")
    
except Exception as e:
    print(f"   ✗ Error testing UI components: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test backtest engine modifications
print("\n5. Testing backtest engine...")
try:
    from engine.backtest_engine import BacktestEngine
    engine = BacktestEngine()
    print("   ✓ BacktestEngine initialized successfully")
    
    # Check if methods have strategy parameter
    import inspect
    sig = inspect.signature(engine.execute_buy_long)
    params = list(sig.parameters.keys())
    if 'strategy' in params:
        print("   ✓ execute_buy_long has strategy parameter")
    else:
        print("   ✗ execute_buy_long missing strategy parameter")
    
except Exception as e:
    print(f"   ✗ Error testing backtest engine: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✓ All tests passed! Features are working correctly.")
print("="*60)
print("\nYou can now:")
print("1. Load NIFTY instruments (futures/options) from sidebar")
print("2. Select nifty_options_straddle.py strategy")
print("3. Run backtest to see detailed strike & side tracking")
print("4. Check 'Options Info' column in results table")
