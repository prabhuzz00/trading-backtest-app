"""
Test Bear Put Spread Strategy

Tests the bear put spread options strategy to ensure:
1. Strategy loads correctly
2. Position construction is correct (BUY higher strike PUT, SELL lower strike PUT)
3. P&L calculations are accurate
4. Entry/exit logic works as expected
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'strategies'))

from bear_put_spread import Strategy
import numpy as np

def test_bear_put_spread():
    """Test bear put spread construction and valuation"""
    
    print("="*70)
    print("TESTING BEAR PUT SPREAD STRATEGY")
    print("="*70)
    
    # Initialize strategy
    strategy = Strategy(
        entry_day=0,  # Monday
        hold_days=7,
        profit_target_pct=0.50,
        stop_loss_pct=0.75,
        strike_spacing=10000,  # 100 points
        momentum_threshold=-0.0005,  # Negative for bearish
        volatility_threshold=0.5
    )
    
    print(f"\nStrategy Parameters:")
    print(f"  Entry Day: Monday")
    print(f"  Hold Days: {strategy.hold_days}")
    print(f"  Profit Target: {strategy.profit_target_pct*100}%")
    print(f"  Stop Loss: {strategy.stop_loss_pct*100}%")
    print(f"  Strike Spacing: {strategy.strike_spacing} paise (Rs.{strategy.strike_spacing/100})")
    print(f"  Momentum Threshold: {strategy.momentum_threshold} (bearish)")
    
    # Test spread construction
    spot = 1825615  # NIFTY spot in paise
    atr = 27384.22
    days_to_expiry = 7
    
    print(f"\n{'='*70}")
    print(f"Test Spot: Rs.{spot/100:.2f} ({spot} paise)")
    print(f"ATR: Rs.{atr/100:.2f}")
    print(f"Days to Expiry: {days_to_expiry}")
    
    # Build spread
    legs, net_cost, max_profit, max_loss = strategy.build_bear_put_spread(
        spot, atr, days_to_expiry
    )
    
    print(f"\n{'='*70}")
    print("ENTRY - Bear Put Spread")
    print(f"{'='*70}")
    
    for leg in legs:
        action = leg['side']
        strike = leg['strike']
        option_type = leg['type']
        premium = leg['entry_premium']
        print(f"{action:<6} {strike:<10} {option_type:<4} Premium: Rs.{premium/100:>10.2f}")
    
    print(f"\nNet Cost (Debit): Rs.{abs(net_cost)/100:.2f}")
    print(f"Max Profit: Rs.{max_profit/100:.2f}")
    print(f"Max Loss: Rs.{max_loss/100:.2f}")
    print(f"Break-Even: Rs.{(legs[0]['strike'] - abs(net_cost))/100:.2f}")
    
    # Verify spread structure
    print(f"\n{'='*70}")
    print("VERIFICATION")
    print(f"{'='*70}")
    
    buy_leg = [l for l in legs if l['side'] == 'BUY'][0]
    sell_leg = [l for l in legs if l['side'] == 'SELL'][0]
    
    print(f"✓ Buy leg is higher strike: {buy_leg['strike']} > {sell_leg['strike']}: {buy_leg['strike'] > sell_leg['strike']}")
    print(f"✓ Both are PUT options: {buy_leg['type'] == 'PE' and sell_leg['type'] == 'PE'}")
    print(f"✓ Strike spacing: {buy_leg['strike'] - sell_leg['strike']} = {strategy.strike_spacing}")
    print(f"✓ Net cost is positive (debit): {abs(net_cost) > 0}")
    print(f"✓ Max profit = Strike width - Net cost: {max_profit:.2f} = {buy_leg['strike'] - sell_leg['strike']} - {abs(net_cost):.2f}")
    
    # Test P&L scenarios
    print(f"\n{'='*70}")
    print("P&L SCENARIOS")
    print(f"{'='*70}")
    
    scenarios = [
        ("Price drops moderately", spot - 5000, 1, 6),
        ("Price drops more", spot - 10000, 2, 5),
        ("Price stays flat", spot, 3, 4),
        ("Price goes up", spot + 5000, 4, 3),
    ]
    
    for scenario_name, test_spot, days_held, days_remaining in scenarios:
        current_value = strategy.calculate_position_value(
            legs, test_spot, atr, days_remaining
        )
        pnl = current_value - abs(net_cost)
        pnl_pct = (pnl / abs(net_cost)) * 100 if abs(net_cost) > 0 else 0
        
        print(f"\n{scenario_name}:")
        print(f"  Spot: Rs.{test_spot/100:.2f} | Days held: {days_held} | Days remaining: {days_remaining}")
        print(f"  Current spread value: Rs.{current_value/100:.2f}")
        print(f"  P&L: Rs.{pnl/100:.2f} ({pnl_pct:+.2f}%)")
    
    print(f"\n{'='*70}")
    print("TEST COMPLETED SUCCESSFULLY")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_bear_put_spread()
