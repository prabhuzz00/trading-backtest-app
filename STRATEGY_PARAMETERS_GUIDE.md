# Quick Reference: Advanced Options Strategies Parameters

## Strategy Comparison Table

| Strategy | Type | Default Hold Days | Capital Req | Risk Level | Best Market |
|----------|------|-------------------|-------------|------------|-------------|
| Short Vol Inventory | Premium Seller | 7 | High | High | Range/Low Vol |
| Short Put Ladder | Premium Seller | 7 | Very High | Very High | Neutral-Bearish |
| Tail Wing Hedge | Protective | 14 | Low | Low | Any (Protection) |
| Premium Band | Iron Condor | 7 | Medium | Medium | Range/Low Vol |
| Risk Reversal | Directional | 10 | Low | Medium | Bullish |
| Carry Backspread | Directional | 10 | Low | Medium | Bullish/Volatile |

---

## 1. Short Vol Inventory (Strike Grid)

### Key Parameters
```python
ShortVolInventory(
    entry_day=None,              # Any day (None) or specific weekday (0-4)
    hold_days=7,                 # 5-14 days typical
    num_strikes=5,               # 3-7 strikes recommended
    strike_spacing_pct=0.02,     # 1-3% typical (0.01-0.03)
    sell_both_sides=True,        # True for both calls/puts
    profit_target_pct=0.60,      # 50-70% of max profit (0.50-0.70)
    stop_loss_pct=2.0,           # 150-250% of credit (1.5-2.5)
    max_aggregate_delta=0.5,     # 0.3-0.7 delta range
    lot_size=75                  # Nifty standard lot
)
```

### Tuning Tips
- **More strikes**: More premium but more risk
- **Wider spacing**: Less correlation, more independent legs
- **Both sides off**: Use when directional bias exists
- **Lower delta limit**: More neutral positioning

---

## 2. Short Put Ladder/Strip

### Key Parameters
```python
ShortPutLadder(
    entry_day=None,
    hold_days=7,                 # 5-10 days typical
    num_strikes=3,               # 2-4 levels recommended
    strike_spacing_pct=0.03,     # 2-5% typical (0.02-0.05)
    ratio_multiplier=1.5,        # 1.3-2.0 ratio range
    profit_target_pct=0.60,      # 50-70% of max profit
    stop_loss_pct=2.0,           # 150-250% of credit
    base_delta=0.30,             # 0.25-0.35 for highest strike
    lot_size=75
)
```

### Tuning Tips
- **Higher ratio**: More aggressive, more downside exposure
- **More strikes**: Smoother ladder, more capital required
- **Tighter spacing**: More concentrated risk zone
- **Higher base delta**: Closer to ATM, more premium

---

## 3. Tail Wing Hedge

### Key Parameters
```python
TailWingHedge(
    entry_day=None,
    hold_days=14,                # 10-30 days typical
    tail_strike_pct=0.10,        # 7-15% OTM (0.07-0.15)
    wing_strike_pct=0.03,        # 2-5% OTM (0.02-0.05)
    wing_ratio=2.0,              # 1.5-3.0 ratio range
    max_debit_pct=0.005,         # 0.3-1.0% max cost (0.003-0.01)
    profit_target_multiple=3.0,  # 2-5x target
    lot_size=75
)
```

### Tuning Tips
- **Further tail**: Cheaper but less responsive
- **Closer wing**: More premium but more risk if tested
- **Higher ratio**: More financing, more risk
- **Longer hold**: Better for monthly hedges

---

## 4. Risk-Defined Short Premium Band (Iron Condor)

### Key Parameters
```python
RiskDefinedPremiumBand(
    entry_day=None,
    hold_days=7,                 # 5-14 days typical
    band_width_pct=0.10,         # 8-15% band (0.08-0.15)
    spread_width_pct=0.02,       # 1-3% spread (0.01-0.03)
    profit_target_pct=0.50,      # 40-60% of max profit
    stop_loss_pct=2.0,           # 150-300% of credit
    target_delta=0.20,           # 0.15-0.25 delta range
    lot_size=75
)
```

### Tuning Tips
- **Wider band**: More room but less premium
- **Wider spreads**: Lower risk/reward ratio
- **Higher delta**: More premium but more risk
- **Earlier profit target**: Higher win rate, lower total return

---

## 5. Bullish Risk Reversal

### Key Parameters
```python
BullishRiskReversal(
    entry_day=None,
    hold_days=10,                # 7-14 days typical
    call_otm_pct=0.05,           # 3-7% OTM (0.03-0.07)
    put_otm_pct=0.05,            # 3-7% OTM (0.03-0.07)
    max_debit_pct=0.01,          # 0.5-2% max cost (0.005-0.02)
    profit_target_pct=1.0,       # 50-150% target (0.5-1.5)
    stop_loss_pct=0.50,          # 40-60% stop (0.4-0.6)
    momentum_lookback=10,        # 5-20 days
    lot_size=75
)
```

### Tuning Tips
- **Closer calls**: More delta, higher cost
- **Asymmetric strikes**: Adjust bias (e.g., 3% call, 7% put)
- **Longer lookback**: Smoother momentum signal
- **Higher profit target**: Let winners run more

---

## 6. Bullish Carry + Call Backspread

### Key Parameters
```python
BullishCarryCallBackspread(
    entry_day=None,
    hold_days=10,                # 7-14 days typical
    short_call_otm_pct=0.02,     # 1-3% OTM (0.01-0.03)
    long_call_otm_pct=0.05,      # 4-7% OTM (0.04-0.07)
    backspread_ratio=2.0,        # 1.5-3.0 ratio
    max_debit_pct=0.005,         # 0-1% max cost (0-0.01)
    profit_target_pct=2.0,       # 150-300% target (1.5-3.0)
    stop_loss_pct=0.75,          # 50-100% stop (0.5-1.0)
    momentum_threshold=0.01,     # 0.5-2% threshold (0.005-0.02)
    lot_size=75
)
```

### Tuning Tips
- **Higher ratio**: More unlimited upside, more cost
- **Wider strike gap**: Smaller danger zone
- **Lower momentum threshold**: More entries
- **Tighter profit target**: Don't get caught in danger zone

---

## Common Parameters Across Strategies

### Timing Parameters
- `entry_day`: None (any day) or 0-4 (Mon-Fri)
- `hold_days`: Holding period before time-based exit
- `min_days_to_expiry`: Minimum DTE to enter (default: 7)
- `max_days_to_expiry`: Maximum DTE to enter (default: 30)

### Strike Parameters
- `strike_step`: Rounding increment (default: 5000 = 50 points)
- `lot_size`: Contract size (Nifty default: 75)

### Exit Parameters
- `profit_target_pct`: % profit to exit (as decimal)
- `stop_loss_pct`: % loss to exit (as decimal)

---

## Parameter Optimization Tips

### Risk Management
1. **Start Conservative**: Use lower lot sizes initially
2. **Test Different Windows**: Try various hold_days (7, 10, 14)
3. **Adjust Targets**: Higher profit targets = lower win rate but better trades
4. **Monitor Drawdown**: Keep max_drawdown under 15-20%

### Market Conditions
- **High IV**: Favor premium selling strategies (1, 2, 4)
- **Low IV**: Favor long volatility strategies (3, 6)
- **Trending**: Use directional strategies (5, 6)
- **Range-bound**: Use neutral strategies (1, 4)

### Position Sizing
- **Complex Strategies** (1, 2, 6): Use smaller position sizes
- **Simple Strategies** (3, 5): Can use larger positions
- **Multiple Legs**: Divide capital by number of legs

### Backtesting Focus
1. **Win Rate**: Target 50-65% for most strategies
2. **Avg Win/Loss Ratio**: Target > 1.5:1
3. **Max Drawdown**: Keep under 20%
4. **Sharpe Ratio**: Target > 1.0
5. **Trade Frequency**: Balance between overtrading and underutilization

---

## Quick Strategy Selection Guide

### Choose based on:

**Market Volatility:**
- High IV → Strategies 1, 2, 4
- Low IV → Strategies 3, 6

**Market Direction:**
- Bullish → Strategies 5, 6
- Neutral → Strategies 1, 4
- Bearish → Strategy 2
- Uncertain → Strategy 3

**Capital Available:**
- High → Strategies 1, 2
- Medium → Strategy 4
- Low → Strategies 3, 5, 6

**Risk Tolerance:**
- Conservative → Strategies 3, 4
- Moderate → Strategies 5, 6
- Aggressive → Strategies 1, 2

**Time Commitment:**
- Active management → Strategies 1, 2
- Moderate → Strategies 4, 5, 6
- Passive → Strategy 3

---

## Example Configurations

### Conservative Portfolio
```python
# 40% Capital: Premium Band (safe income)
# 30% Capital: Tail Hedge (protection)
# 30% Capital: Risk Reversal (directional)
```

### Aggressive Portfolio
```python
# 50% Capital: Short Vol Inventory (high premium)
# 30% Capital: Carry Backspread (upside)
# 20% Capital: Short Put Ladder (enhanced yield)
```

### Balanced Portfolio
```python
# 35% Capital: Premium Band
# 35% Capital: Risk Reversal
# 20% Capital: Tail Hedge
# 10% Capital: Carry Backspread
```

---

For detailed strategy explanations, see `ADVANCED_OPTIONS_STRATEGIES.md`
