"""
Debug spread valuation with lot size
"""
import sys
sys.path.insert(0, 'strategies')

from bull_call_spread import Strategy

strategy = Strategy(lot_size=75)

spot = 1825945  # Entry spot
atr = 27384.22
days_to_expiry = 7

print(f"Spot: {spot} paise = Rs.{spot/100:.2f}")
print(f"ATR: {atr:.2f} paise = Rs.{atr/100:.2f}")
print(f"Lot Size: {strategy.lot_size}")
print(f"Strike Spacing: {strategy.strike_spacing} paise = Rs.{strategy.strike_spacing/100:.2f}")
print()

# Build spread
legs, net_cost, max_profit, max_loss = strategy.build_bull_call_spread(
    spot, atr, days_to_expiry
)

print("="*70)
print("ENTRY SPREAD")
print("="*70)
for leg in legs:
    print(f"{leg['side']:<6} {leg['strike']:>10} {leg['type']:<4} Premium: {leg['entry_premium']:>10.2f} paise (Rs.{leg['entry_premium']/100:.2f}) x {leg['quantity']}")

print(f"\nNet Cost (Debit): {abs(net_cost):.2f} paise = Rs.{abs(net_cost)/100:.2f}")
print(f"Max Profit: {max_profit:.2f} paise = Rs.{max_profit/100:.2f}")
print(f"Max Loss: {max_loss:.2f} paise = Rs.{max_loss/100:.2f}")

# Calculate exit value after 1 minute (profit target scenario)
exit_spot = 1825500  # Dropped slightly
days_remaining = 6

print(f"\n{'='*70}")
print(f"EXIT SCENARIO (1 minute later, price dropped to Rs.{exit_spot/100:.2f})")
print(f"{'='*70}")

current_value = strategy.calculate_position_value(legs, exit_spot, atr, days_remaining)
pnl = current_value - abs(net_cost)
pnl_pct = (pnl / abs(net_cost)) * 100

print(f"Current Spread Value: {current_value:.2f} paise = Rs.{current_value/100:.2f}")
print(f"P&L: {pnl:.2f} paise = Rs.{pnl/100:.2f} ({pnl_pct:+.2f}%)")

# Check individual leg values at exit
print(f"\nIndividual leg values at exit:")
for leg in legs:
    current_premium = strategy.estimate_option_premium(
        exit_spot, leg['strike'], atr, leg['type'], days_remaining
    )
    print(f"{leg['side']:<6} {leg['strike']:>10} {leg['type']:<4} Current: {current_premium:>10.2f} paise (Rs.{current_premium/100:.2f}) x {leg['quantity']} = {current_premium * leg['quantity']:.2f} paise (Rs.{current_premium * leg['quantity']/100:.2f})")
