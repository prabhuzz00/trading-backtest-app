"""
Test the updated OptionsBacktestEngine from GUI context
"""
import sys
sys.path.insert(0, 'src')

from engine.options_backtest_engine import OptionsBacktestEngine
from utils.db_connection import get_stock_data

print("="*80)
print("TESTING OPTIONS BACKTEST ENGINE (GUI VERSION)")
print("="*80)

# Test with Risk Defined Premium Band (we know this works)
strategy_path = 'strategies/risk_defined_premium_band.py'
symbol = 'NSECM:NIFTY 50'
start_date = '2024-06-01'  # Longer period
end_date = '2024-12-31'

def progress_callback(pct, msg):
    print(f"[{pct:3d}%] {msg}")

print(f"\nStrategy: {strategy_path}")
print(f"Symbol: {symbol}")
print(f"Period: {start_date} to {end_date}\n")

try:
    engine = OptionsBacktestEngine(initial_cash=100000)
    
    results = engine.run_backtest(
        strategy_path,
        symbol,
        start_date,
        end_date,
        progress_callback=progress_callback
    )
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    print(f"Total Return: {results.get('total_return', 0):.2f}%")
    print(f"Total Trades: {results.get('total_trades', 0)}")
    print(f"Winning Trades: {results.get('winning_trades', 0)}")
    print(f"Losing Trades: {results.get('losing_trades', 0)}")
    print(f"Win Rate: {results.get('win_rate', 0):.2f}%")
    print(f"Total P&L: ₹{results.get('total_pnl', 0):,.2f}")
    print(f"Final Equity: ₹{results.get('final_equity', 100000):,.2f}")
    
    print(f"\nTrade Details:")
    trades = results.get('trades', [])
    for i, trade in enumerate(trades[:5], 1):  # Show first 5 trades
        print(f"\n  Trade {i}:")
        print(f"    Date: {trade.get('date')}")
        print(f"    Action: {trade.get('action')}")
        print(f"    Type: {trade.get('type')}")
        if 'pnl' in trade:
            print(f"    P&L: ₹{trade.get('pnl', 0):,.2f}")
    
    if len(trades) > 5:
        print(f"\n  ... and {len(trades) - 5} more trades")
    
    print("\n✅ SUCCESS - Engine is working!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
