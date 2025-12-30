"""
Test Bull Call Spread Strategy

This script tests the bull call spread options strategy against NIFTY data
to verify it works correctly with the backtesting engine.
"""

import sys
sys.path.insert(0, r'd:\project\trading-backtest-app\src')
sys.path.insert(0, r'd:\project\trading-backtest-app')

from engine.backtest_engine import BacktestEngine
from datetime import datetime

def test_bull_call_spread():
    """Test bull call spread strategy"""
    
    print("=" * 80)
    print("Testing Bull Call Spread Options Strategy")
    print("=" * 80)
    
    # Initialize backtest engine
    engine = BacktestEngine(initial_cash=100000, brokerage_rate=0.00007)
    
    # Strategy parameters
    strategy_path = r"d:\project\trading-backtest-app\strategies\bull_call_spread.py"
    
    # Test with NIFTY data (using the underlying index for simulation)
    # Note: Using NIFTY futures as the underlying
    stock_symbol = "NSEFO:NIFTY1"  # NIFTY futures
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    print(f"\nBacktest Parameters:")
    print(f"  Symbol: {stock_symbol}")
    print(f"  Period: {start_date} to {end_date}")
    print(f"  Initial Cash: Rs.100,000")
    print(f"  Strategy: Bull Call Spread")
    print("\nStrategy Configuration:")
    print(f"  Entry Day: Monday (0)")
    print(f"  Hold Days: 7 days")
    print(f"  Strike Spacing: 100 points")
    print(f"  Profit Target: 50%")
    print(f"  Stop Loss: 75%")
    print(f"  Momentum Threshold: 1%")
    print("=" * 80)
    
    try:
        # Run backtest
        print("\nRunning backtest...")
        results = engine.run_backtest(
            strategy_path=strategy_path,
            stock_symbol=stock_symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        # Display results
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)
        
        metrics = results['metrics']
        
        print(f"\n[Performance Metrics]:")
        print(f"  Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"  Final Portfolio Value: Rs.{metrics.get('final_value', 0):,.2f}")
        print(f"  Total P&L: Rs.{metrics.get('total_pnl', 0):,.2f}")
        
        print(f"\n[Trade Statistics]:")
        print(f"  Total Trades: {metrics.get('total_trades', 0)}")
        print(f"  Winning Trades: {metrics.get('winning_trades', 0)}")
        print(f"  Losing Trades: {metrics.get('losing_trades', 0)}")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
        
        print(f"\n[Profit Analysis]:")
        print(f"  Average Win: Rs.{metrics.get('avg_win', 0):,.2f}")
        print(f"  Average Loss: Rs.{metrics.get('avg_loss', 0):,.2f}")
        print(f"  Largest Win: Rs.{metrics.get('largest_win', 0):,.2f}")
        print(f"  Largest Loss: Rs.{metrics.get('largest_loss', 0):,.2f}")
        
        print(f"\n[Risk Metrics]:")
        print(f"  Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        
        # Display trade details
        trades = results.get('trades', [])
        if trades:
            print(f"\n[Trade Details (First 10 trades)]:")
            print("-" * 80)
            print(f"{'Date':<12} {'Action':<10} {'Price':<10} {'P&L':<12} {'Options Info':<30}")
            print("-" * 80)
            
            for i, trade in enumerate(trades[:10]):
                date = str(trade.get('date', ''))[:10]
                action = trade.get('action', '')
                price = trade.get('price', 0)
                pnl = trade.get('pnl', 0)
                options_info = trade.get('options_info', '')[:30]
                
                print(f"{date:<12} {action:<10} {price:<10.2f} {pnl:<12.2f} {options_info:<30}")
            
            if len(trades) > 10:
                print(f"... and {len(trades) - 10} more trades")
        
        print("\n" + "=" * 80)
        print("SUCCESS: Bull Call Spread Strategy Test Completed Successfully!")
        print("=" * 80)
        
        return results
        
    except Exception as e:
        print(f"\nERROR during backtest: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_with_different_parameters():
    """Test with different strike spacings and parameters"""
    
    print("\n\n" + "=" * 80)
    print("Testing Different Bull Call Spread Configurations")
    print("=" * 80)
    
    # Test configurations
    configs = [
        {"strike_spacing": 50, "profit_target_pct": 0.40, "name": "Narrow Spread (50pts)"},
        {"strike_spacing": 100, "profit_target_pct": 0.50, "name": "Medium Spread (100pts)"},
        {"strike_spacing": 150, "profit_target_pct": 0.60, "name": "Wide Spread (150pts)"},
    ]
    
    print("\nThis would test multiple configurations to find optimal parameters.")
    print("Configuration options:")
    for i, config in enumerate(configs, 1):
        print(f"  {i}. {config['name']}")
        print(f"     - Strike Spacing: {config['strike_spacing']} points")
        print(f"     - Profit Target: {config['profit_target_pct']*100:.0f}%")
    
    print("\nNote: Modify the Strategy class initialization in bull_call_spread.py")
    print("      to change these parameters for testing.")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Bull Call Spread Options Strategy - Backtesting System")
    print("=" * 80 + "\n")
    
    # Run basic test
    results = test_bull_call_spread()
    
    # Show parameter testing info
    if results:
        test_with_different_parameters()
    
    print("\n\nTest script completed!")
