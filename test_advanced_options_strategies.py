"""
Test script for all 6 advanced Nifty 50 options strategies

This script tests:
1. Short Vol Inventory (Strike Grid)
2. Short Put Ladder/Strip
3. Tail Wing Hedge
4. Risk-Defined Short Premium Band
5. Bullish Risk Reversal
6. Bullish Carry + Call Backspread

Usage:
    python test_advanced_options_strategies.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies.short_vol_inventory import Strategy as ShortVolInventory
from strategies.short_put_ladder import Strategy as ShortPutLadder
from strategies.tail_wing_hedge import Strategy as TailWingHedge
from strategies.risk_defined_premium_band import Strategy as RiskDefinedPremiumBand
from strategies.bullish_risk_reversal import Strategy as BullishRiskReversal
from strategies.bullish_carry_call_backspread import Strategy as BullishCarryCallBackspread

from src.engine.backtest_engine import BacktestEngine
import pandas as pd

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def test_strategy(strategy_name, strategy_instance, start_date, end_date, initial_capital=1000000):
    """
    Test a single strategy
    
    Args:
        strategy_name: Name of the strategy
        strategy_instance: Initialized strategy object
        start_date: Backtest start date
        end_date: Backtest end date
        initial_capital: Starting capital
    """
    print_section(f"Testing {strategy_name}")
    
    try:
        # Create backtest engine
        engine = BacktestEngine(
            strategy=strategy_instance,
            symbol='NIFTY',
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            data_source='mongodb'
        )
        
        print(f"Strategy: {strategy_name}")
        print(f"Symbol: NIFTY")
        print(f"Period: {start_date} to {end_date}")
        print(f"Initial Capital: ₹{initial_capital:,.0f}")
        print("\nRunning backtest...")
        
        # Run backtest
        results = engine.run()
        
        if results:
            print("\n--- Backtest Results ---")
            print(f"Total Trades: {results.get('total_trades', 0)}")
            print(f"Winning Trades: {results.get('winning_trades', 0)}")
            print(f"Losing Trades: {results.get('losing_trades', 0)}")
            
            win_rate = results.get('win_rate', 0) * 100
            print(f"Win Rate: {win_rate:.2f}%")
            
            total_pnl = results.get('total_pnl', 0)
            print(f"Total P&L: ₹{total_pnl:,.2f}")
            
            total_return = results.get('total_return_pct', 0) * 100
            print(f"Total Return: {total_return:.2f}%")
            
            avg_profit = results.get('avg_profit', 0)
            print(f"Average Profit per Trade: ₹{avg_profit:,.2f}")
            
            max_drawdown = results.get('max_drawdown', 0) * 100
            print(f"Max Drawdown: {max_drawdown:.2f}%")
            
            sharpe_ratio = results.get('sharpe_ratio', 0)
            print(f"Sharpe Ratio: {sharpe_ratio:.3f}")
            
            # Trade log
            trade_log = strategy_instance.get_trade_log()
            if trade_log:
                print(f"\nTrade Log Entries: {len(trade_log)}")
                
                # Show first few trades
                print("\nFirst 3 Trades:")
                for i, trade in enumerate(trade_log[:6]):  # Show entry + exit for 3 trades
                    print(f"  {i+1}. {trade.get('action', 'N/A')} - Date: {trade.get('date', 'N/A')} - "
                          f"Spot: {trade.get('spot', 0):.2f}")
            
            print("\n✓ Test completed successfully")
            return True
            
        else:
            print("\n✗ No results returned from backtest")
            return False
            
    except Exception as e:
        print(f"\n✗ Error during backtest: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print_section("Advanced Nifty 50 Options Strategies - Comprehensive Test Suite")
    
    # Test configuration
    # Use a recent period with good data availability
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')  # 3 months
    initial_capital = 1000000  # 10 lakhs
    
    print(f"Test Period: {start_date} to {end_date}")
    print(f"Initial Capital: ₹{initial_capital:,.0f}")
    print(f"Underlying: Nifty 50 Options")
    
    # Track results
    test_results = {}
    
    # 1. Short Vol Inventory (Strike Grid)
    print_section("Test 1/6: Short Vol Inventory (Strike Grid)")
    strategy1 = ShortVolInventory(
        entry_day=None,  # Any day for testing
        hold_days=7,
        num_strikes=3,  # Reduced for testing
        strike_spacing_pct=0.02,
        sell_both_sides=True,
        profit_target_pct=0.60,
        stop_loss_pct=2.0,
        lot_size=75
    )
    test_results['Short Vol Inventory'] = test_strategy(
        "Short Vol Inventory (Strike Grid)", 
        strategy1, 
        start_date, 
        end_date, 
        initial_capital
    )
    
    # 2. Short Put Ladder/Strip
    print_section("Test 2/6: Short Put Ladder/Strip")
    strategy2 = ShortPutLadder(
        entry_day=None,
        hold_days=7,
        num_strikes=3,
        strike_spacing_pct=0.03,
        ratio_multiplier=1.5,
        profit_target_pct=0.60,
        stop_loss_pct=2.0,
        lot_size=75
    )
    test_results['Short Put Ladder'] = test_strategy(
        "Short Put Ladder/Strip", 
        strategy2, 
        start_date, 
        end_date, 
        initial_capital
    )
    
    # 3. Tail Wing Hedge
    print_section("Test 3/6: Tail Wing Hedge")
    strategy3 = TailWingHedge(
        entry_day=None,
        hold_days=14,
        tail_strike_pct=0.10,
        wing_strike_pct=0.03,
        wing_ratio=2.0,
        max_debit_pct=0.005,
        profit_target_multiple=3.0,
        lot_size=75
    )
    test_results['Tail Wing Hedge'] = test_strategy(
        "Tail Wing Hedge", 
        strategy3, 
        start_date, 
        end_date, 
        initial_capital
    )
    
    # 4. Risk-Defined Short Premium Band
    print_section("Test 4/6: Risk-Defined Short Premium Band")
    strategy4 = RiskDefinedPremiumBand(
        entry_day=None,
        hold_days=7,
        band_width_pct=0.10,
        spread_width_pct=0.02,
        profit_target_pct=0.50,
        stop_loss_pct=2.0,
        lot_size=75
    )
    test_results['Premium Band'] = test_strategy(
        "Risk-Defined Short Premium Band", 
        strategy4, 
        start_date, 
        end_date, 
        initial_capital
    )
    
    # 5. Bullish Risk Reversal
    print_section("Test 5/6: Bullish Risk Reversal")
    strategy5 = BullishRiskReversal(
        entry_day=None,
        hold_days=10,
        call_otm_pct=0.05,
        put_otm_pct=0.05,
        max_debit_pct=0.01,
        profit_target_pct=1.0,
        stop_loss_pct=0.50,
        momentum_lookback=10,
        lot_size=75
    )
    test_results['Risk Reversal'] = test_strategy(
        "Bullish Risk Reversal", 
        strategy5, 
        start_date, 
        end_date, 
        initial_capital
    )
    
    # 6. Bullish Carry + Call Backspread
    print_section("Test 6/6: Bullish Carry + Call Backspread")
    strategy6 = BullishCarryCallBackspread(
        entry_day=None,
        hold_days=10,
        short_call_otm_pct=0.02,
        long_call_otm_pct=0.05,
        backspread_ratio=2.0,
        max_debit_pct=0.005,
        profit_target_pct=2.0,
        stop_loss_pct=0.75,
        momentum_threshold=0.01,
        lot_size=75
    )
    test_results['Carry Backspread'] = test_strategy(
        "Bullish Carry + Call Backspread", 
        strategy6, 
        start_date, 
        end_date, 
        initial_capital
    )
    
    # Summary
    print_section("Test Summary")
    
    successful = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print(f"Tests Completed: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"\nSuccess Rate: {(successful/total)*100:.1f}%")
    
    print("\nIndividual Results:")
    for strategy_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {strategy_name}")
    
    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80 + "\n")
    
    # Return exit code
    return 0 if successful == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
