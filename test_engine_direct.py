"""
Test strategy signals directly to debug UI issue
"""
import sys
sys.path.insert(0, r'd:\project\trading-backtest-app\src')
sys.path.insert(0, r'd:\project\trading-backtest-app')

from utils.db_connection import get_stock_data
from engine.backtest_engine import BacktestEngine

print("="*80)
print("TESTING BACKTEST ENGINE DIRECTLY")
print("="*80)

# Use exact same setup as UI
engine = BacktestEngine(initial_cash=100000, brokerage_rate=0.00007)

print("\nRunning backtest through engine...")
try:
    results = engine.run_backtest(
        strategy_path="strategies/bull_call_spread.py",
        stock_symbol="NSEFO:NIFTY1",
        start_date="2023-01-02",
        end_date="2023-01-03"
    )
    
    print(f"\nResults:")
    print(f"  Total trades: {len(results['trades'])}")
    print(f"  Metrics: {results['metrics'].get('total_trades', 0)}")
    
    if results['trades']:
        print(f"\nFirst 10 trades with details:")
        for i, trade in enumerate(results['trades'][:10]):
            action = trade['action']
            print(f"\n  {i+1}. {trade['date']} - {action}")
            print(f"     Price: Rs.{trade['price']:,.2f}")
            print(f"     Value: Rs.{trade['value']:,.2f}")
            print(f"     Brokerage: Rs.{trade['brokerage']:,.2f}")
            if action in ['SELL', 'SELL_LONG']:
                print(f"     P&L: Rs.{trade['pnl']:,.2f} ({trade['pnl_pct']:.2f}%)")
            if trade.get('options_info'):
                print(f"     Options: {trade['options_info']}")
    else:
        print("\n  NO TRADES FOUND!")
        print("\n  Checking portfolio state...")
        
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
