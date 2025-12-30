"""
Test spread valuation logic
"""
import sys
sys.path.insert(0, 'strategies')
from bull_call_spread import Strategy

# Create strategy
strategy = Strategy()

# Test entry
spot = 1825615  # NIFTY at 18256.15
atr = spot * 0.015  # 1.5% ATR

print(f"Spot: {spot}")
print(f"ATR: {atr:.2f}")
print()

# Build spread
legs, net_cost, max_profit, max_loss = strategy.build_bull_call_spread(spot, atr, days_to_expiry=7)

print("=" * 70)
print("ENTRY - Bull Call Spread")
print("=" * 70)
for leg in legs:
    print(f"{leg['side']:<6} {leg['strike']:<10} {leg['type']:<4} Premium: {leg['entry_premium']:>10.2f}")
print(f"\nNet Cost (Debit): {abs(net_cost):.2f}")
print(f"Max Profit: {max_profit:.2f}")
print(f"Max Loss: {max_loss:.2f}")
print()

# Simulate different exit scenarios
print("=" * 70)
print("EXIT SCENARIOS")
print("=" * 70)

scenarios = [
    ("Slightly up", 1826000, 1),   # Price up, 1 day later
    ("More up", 1827000, 2),       # Price more up, 2 days later
    ("Flat", 1825615, 3),          # No movement, 3 days later
    ("Down", 1824000, 4),          # Price down, 4 days later
]

for name, exit_spot, days_held in scenarios:
    days_remaining = max(1, 7 - days_held)
    exit_atr = exit_spot * 0.015
    
    current_value = strategy.calculate_position_value(legs, exit_spot, exit_atr, days_remaining)
    pnl = current_value - abs(net_cost)
    pnl_pct = (pnl / abs(net_cost)) * 100 if abs(net_cost) > 0 else 0
    
    print(f"\n{name}:")
    print(f"  Spot: {exit_spot} | Days held: {days_held} | Days remaining: {days_remaining}")
    print(f"  Current spread value: {current_value:.2f}")
    print(f"  P&L: {pnl:.2f} ({pnl_pct:+.2f}%)")
