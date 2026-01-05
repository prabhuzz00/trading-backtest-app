"""
Test Short Strangle Strategy

This script tests the short strangle options strategy which benefits from theta decay.

The strategy:
- SELLS an OTM call option
- SELLS an OTM put option
- Collects premium from both
- Profits when underlying stays within range (time decay)

Usage:
    python test_short_strangle.py
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.db_connection import get_stock_data
from strategies.short_strangle import Strategy

def test_short_strangle():
    """Test short strangle strategy with NIFTY data"""
    
    print("=" * 80)
    print("SHORT STRANGLE STRATEGY TEST - Theta Decay Strategy")
    print("=" * 80)
    print()
    print("Strategy Overview:")
    print("  - Sells OTM Call + Sells OTM Put")
    print("  - Collects premium from both options")
    print("  - Profits from TIME DECAY (theta)")
    print("  - Best in low volatility, range-bound markets")
    print("  - Expiry: Every Thursday (NIFTY50 weekly options)")
    print()
    
    # Initialize strategy
    strategy = Strategy(
        entry_day=3,  # Thursday (0=Monday, 3=Thursday)
        hold_days=7,  # Hold for 1 week
        strike_width_pct=0.05,  # 5% away from spot
        profit_target_pct=0.50,  # Close at 50% of max profit
        stop_loss_pct=2.0,  # Stop if loss > 200% of credit
        lot_size=75,
        iv_percentile_max=50,  # Only enter when IV < 50th percentile
        min_days_to_expiry=7,
        max_days_to_expiry=30
    )
    
    print("Strategy Parameters:")
    print(f"  - Entry Day: Thursday (NIFTY weekly expiry)")
    print(f"  - Expiry Day: Next Thursday")
    print(f"  - Strike Width: {strategy.strike_width_pct*100}% from spot")
    print(f"  - Profit Target: {strategy.profit_target_pct*100}% of max profit")
    print(f"  - Stop Loss: {strategy.stop_loss_pct*100}% of credit received")
    print(f"  - Hold Days: {strategy.hold_days}")
    print(f"  - Lot Size: {strategy.lot_size}")
    print(f"  - IV Percentile Max: {strategy.iv_percentile_max}")
    print(f"  - Min Days to Expiry: {strategy.min_days_to_expiry}")
    print(f"  - Max Days to Expiry: {strategy.max_days_to_expiry}")
    print()
    
    # Get NIFTY futures data
    symbol = "NSEFO:NIFTY1"
    start_date = "2020-01-01"
    end_date = "2020-12-31"
    
    print(f"Fetching data for {symbol}...")
    print(f"Period: {start_date} to {end_date}")
    print()
    
    data = get_stock_data(symbol, start_date, end_date, use_cache=True)
    
    if data.empty:
        print("ERROR: No data retrieved. Check symbol and date range.")
        return
    
    print(f"Data loaded: {len(data)} bars")
    print(f"Date range: {data['date'].min()} to {data['date'].max()}")
    print()
    
    # Set underlying symbol
    strategy.set_underlying_symbol(symbol)
    
    # Generate signals
    print("Running backtest...")
    signals = strategy.generate_signals(data)
    
    # Get trade log
    trade_log = strategy.get_trade_log()
    
    print()
    print("=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print()
    
    if trade_log.empty:
        print("No trades generated. Possible reasons:")
        print("  - IV was too high (above 50th percentile)")
        print("  - Insufficient data for entry conditions")
        print("  - No suitable entry days found")
        print()
        print("Try adjusting parameters:")
        print("  - Increase iv_percentile_max")
        print("  - Use different entry_day")
        print("  - Extend date range")
        return
    
    # Separate entries and exits
    entries = trade_log[trade_log['action'] == 'ENTRY']
    exits = trade_log[trade_log['action'] == 'EXIT']
    
    print(f"Total Trades: {len(entries)}")
    print()
    
    if not exits.empty:
        # Calculate statistics
        total_pnl = exits['pnl_total'].sum()
        avg_pnl = exits['pnl_total'].mean()
        win_rate = (exits['pnl_total'] > 0).sum() / len(exits) * 100
        max_win = exits['pnl_total'].max()
        max_loss = exits['pnl_total'].min()
        avg_pnl_pct = exits['pnl_pct'].mean()
        
        print("Performance Summary:")
        print(f"  Total P&L: ₹{total_pnl:,.2f}")
        print(f"  Average P&L per Trade: ₹{avg_pnl:,.2f}")
        print(f"  Average P&L %: {avg_pnl_pct:.2f}%")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Best Trade: ₹{max_win:,.2f}")
        print(f"  Worst Trade: ₹{max_loss:,.2f}")
        print()
        
        # Exit reason breakdown
        print("Exit Reasons:")
        exit_reasons = exits['reason'].value_counts()
        for reason, count in exit_reasons.items():
            pct = count / len(exits) * 100
            print(f"  {reason}: {count} ({pct:.1f}%)")
        print()
    
    # Show trade details
    print("=" * 80)
    print("TRADE DETAILS")
    print("=" * 80)
    print()
    
    for idx, entry in entries.iterrows():
        position_id = entry['position_id']
        exit_row = exits[exits['position_id'] == position_id]
        
        print(f"Trade #{position_id}")
        print(f"  Entry Date: {entry['date']}")
        print(f"  Spot Price: ₹{entry['spot']:,.2f}")
        print(f"  Call Strike: ₹{entry['call_strike']/100:,.0f} (Premium: ₹{entry['call_premium']:,.2f})")
        print(f"  Put Strike: ₹{entry['put_strike']/100:,.0f} (Premium: ₹{entry['put_premium']:,.2f})")
        print(f"  Net Credit Received: ₹{entry['net_credit']:,.2f}")
        print(f"  Max Profit Potential: ₹{entry['net_credit'] * strategy.lot_size:,.2f}")
        print(f"  Days to Expiry: {entry['days_to_expiry']}")
        
        if not exit_row.empty:
            exit_data = exit_row.iloc[0]
            print(f"  Exit Date: {exit_data['date']}")
            print(f"  Exit Spot: ₹{exit_data['spot']:,.2f}")
            print(f"  Exit Reason: {exit_data['reason']}")
            print(f"  Closing Cost: ₹{exit_data['closing_cost']:,.2f}")
            print(f"  P&L: ₹{exit_data['pnl_total']:,.2f} ({exit_data['pnl_pct']:.2f}%)")
            
            # Calculate ROI
            max_risk = entry['net_credit'] * strategy.stop_loss_pct * strategy.lot_size
            roi = (exit_data['pnl_total'] / max_risk) * 100 if max_risk > 0 else 0
            print(f"  ROI: {roi:.2f}%")
        
        print()
    
    print("=" * 80)
    print("STRATEGY BENEFITS FROM THETA DECAY")
    print("=" * 80)
    print()
    print("Key Points:")
    print("  ✓ Collects premium from selling both call and put")
    print("  ✓ Time decay works in your favor (theta positive)")
    print("  ✓ Profits in range-bound, low volatility markets")
    print("  ✓ Best entry: Low IV environments (< 50th percentile)")
    print("  ✓ Exit early: 50% of max profit is excellent risk/reward")
    print()
    print("Risk Management:")
    print("  ⚠ Unlimited loss potential on both sides")
    print("  ⚠ Use stop losses (2x credit received)")
    print("  ⚠ Monitor position - close early if needed")
    print("  ⚠ Avoid before major events/earnings")
    print()

if __name__ == "__main__":
    test_short_strangle()
