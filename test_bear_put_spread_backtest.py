"""
Test Bear Put Spread with Backtest Engine

Tests the bear put spread strategy through the full backtest engine
to ensure proper integration and realistic trade execution.
"""

import sys
sys.path.insert(0, 'src')

from engine.backtest_engine import BacktestEngine

def test_bear_put_spread_backtest():
    """Test bear put spread through backtest engine"""
    
    print("="*80)
    print("TESTING BEAR PUT SPREAD WITH BACKTEST ENGINE")
    print("="*80)
    
    # Initialize engine
    engine = BacktestEngine(initial_cash=100000, brokerage_rate=0.0007)
    
    # Run backtest on NIFTY options data
    print("\nRunning backtest on NIFTY options (January 2023)...")
    print("Looking for bearish momentum to enter bear put spreads...\n")
    
    try:
        results = engine.run_backtest(
            strategy_path="strategies/bear_put_spread.py",
            stock_symbol="NSEFO:NIFTY1",
            start_date="2023-01-02",
            end_date="2023-01-31"
        )
        
        print(f"\nResults:")
        print(f"  Total trades: {len(results['trades'])}")
        print(f"  Metrics: {len(results['metrics'])}")
        
        if results['trades']:
            print(f"\nFirst 10 trades with details:\n")
            for i, trade in enumerate(results['trades'][:10], 1):
                action = trade.get('action', 'UNKNOWN')
                date = trade.get('date', 'N/A')
                price = trade.get('price', 0)
                value = trade.get('value', 0)
                brokerage = trade.get('brokerage', 0)
                
                print(f"  {i}. {date} - {action}")
                print(f"     Price: Rs.{price:,.2f}")
                print(f"     Value: Rs.{value:,.2f}")
                print(f"     Brokerage: Rs.{brokerage:.2f}")
                
                # Show options info if available
                if 'options_info' in trade and trade['options_info']:
                    print(f"     Options: {trade['options_info']}")
                
                # Show P&L for exits
                if action == 'SELL_LONG' and 'pnl' in trade:
                    pnl = trade.get('pnl', 0)
                    pnl_pct = trade.get('pnl_pct', 0)
                    reason = trade.get('reason', '')
                    print(f"     P&L: Rs.{pnl:,.2f} ({pnl_pct:.2f}%)")
                    if reason:
                        print(f"     Options: {trade.get('options_info', '')} ({reason})")
                
                print()
        else:
            print("\n  No trades generated. This could mean:")
            print("  - No bearish momentum detected (momentum >= -0.0005)")
            print("  - Not Monday (entry day)")
            print("  - Insufficient data for indicators")
        
        print("="*80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*80)

if __name__ == "__main__":
    test_bear_put_spread_backtest()
