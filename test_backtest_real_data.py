"""
Test backtest with real options data
"""
import sys
sys.path.append('src')

from engine.options_backtest_engine import OptionsBacktestEngine
from datetime import datetime

def test_backtest_with_real_data():
    """Test a full backtest using real options data"""
    
    print("\n" + "="*80)
    print("Testing Backtest with Real Options Data")
    print("="*80)
    
    # Use Risk-Defined Premium Band strategy
    strategy_path = "strategies/risk_defined_premium_band.py"
    underlying = "NSECM:NIFTY 50"
    
    # Use a date range where we know data exists (2023)
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    print(f"\nStrategy: {strategy_path}")
    print(f"Underlying: {underlying}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ₹100,000")
    
    # Create engine and run backtest
    engine = OptionsBacktestEngine(initial_cash=100000)
    
    def progress(pct, msg):
        print(f"  [{pct:3d}%] {msg}")
    
    try:
        print("\nRunning backtest...")
        results = engine.run_backtest(
            strategy_path=strategy_path,
            stock_symbol=underlying,
            start_date=start_date,
            end_date=end_date,
            progress_callback=progress
        )
        
        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)
        
        print(f"\nTotal Trades: {results['total_trades']}")
        print(f"Winning Trades: {results['winning_trades']}")
        print(f"Losing Trades: {results['losing_trades']}")
        
        if results['total_trades'] > 0:
            win_rate = (results['winning_trades'] / results['total_trades']) * 100
            print(f"Win Rate: {win_rate:.1f}%")
        
        print(f"\nTotal Return: ₹{results['total_return']:,.2f}")
        if 'total_return_pct' in results:
            print(f"Total Return %: {results['total_return_pct']:.2f}%")
        if 'max_drawdown' in results:
            print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        if 'final_value' in results:
            print(f"\nFinal Portfolio Value: ₹{results['final_value']:,.2f}")
        
        # Show sample trades
        if results['trades']:
            print(f"\n\nSample Trades (first 5):")
            print("-" * 80)
            for i, trade in enumerate(results['trades'][:5], 1):
                print(f"\nTrade {i}:")
                print(f"  Date: {trade.get('date', 'N/A')}")
                print(f"  Action: {trade.get('action', 'N/A')}")
                print(f"  Spot: ₹{trade.get('spot', 0):,.2f}")
                
                if 'legs' in trade:
                    print(f"  Legs:")
                    for leg in trade['legs']:
                        print(f"    - {leg.get('action', '')} {leg.get('quantity', 0)} x "
                              f"{leg.get('option_type', '')} {leg.get('strike', 0):,.0f} "
                              f"@ ₹{leg.get('premium', 0):,.2f}")
                
                if 'credit' in trade or 'debit' in trade:
                    amount = trade.get('credit', 0) - trade.get('debit', 0)
                    if amount > 0:
                        print(f"  Net Credit: ₹{amount:,.2f}")
                    else:
                        print(f"  Net Debit: ₹{-amount:,.2f}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n✗ Error during backtest: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*80 + "\n")

if __name__ == "__main__":
    test_backtest_with_real_data()
