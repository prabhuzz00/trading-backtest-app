# Bull Call Spread Strategy - Quick Reference

## What is it?
A **Bull Call Spread** is an options strategy where you:
- **BUY** a call at a lower strike (ITM/ATM) 
- **SELL** a call at a higher strike (OTM)

This creates a debit spread with limited risk and limited profit.

## Quick Example
```
NIFTY at 17,500
BUY 17,500 CE @ ₹150
SELL 17,600 CE @ ₹80
Net Cost: ₹70

Max Profit: ₹30 (when NIFTY > 17,600)
Max Loss: ₹70 (when NIFTY < 17,500)
Breakeven: 17,570
```

## Files Added to Project

1. **`strategies/bull_call_spread.py`** - Main strategy implementation
2. **`test_bull_call_spread.py`** - Test script to verify strategy
3. **`BULL_CALL_SPREAD_GUIDE.md`** - Comprehensive documentation

## How to Use

### Option 1: Via UI
1. Launch the application: `python src/main.py`
2. Select "Bull Call Spread" from strategy dropdown
3. Select stock symbol (e.g., NSEFO-#NIFTY)
4. Set date range
5. Click "Run Backtest"

### Option 2: Via Test Script
```bash
python test_bull_call_spread.py
```

### Option 3: Via Code
```python
from engine.backtest_engine import BacktestEngine

engine = BacktestEngine(initial_cash=100000)
results = engine.run_backtest(
    strategy_path="strategies/bull_call_spread.py",
    stock_symbol="NSEFO-#NIFTY",
    start_date="2020-01-01",
    end_date="2020-12-31"
)
```

## Key Parameters (Adjustable)

Edit `strategies/bull_call_spread.py` to customize:

```python
Strategy(
    entry_day=0,              # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri
    strike_spacing=100,       # Distance between strikes (points)
    profit_target_pct=0.50,   # Take profit at 50%
    stop_loss_pct=0.75,       # Stop loss at 75%
    momentum_threshold=0.01,  # Require 1% upward momentum
    hold_days=7              # Hold for 7 days max
)
```

## When to Use

✅ **Use when:**
- Moderately bullish on market
- Expect 5-10% upward move
- Want to limit risk
- Options are expensive (high IV)

❌ **Avoid when:**
- Expecting explosive moves (profit is capped)
- Very bearish or neutral
- Very short time to expiry

## Strategy Logic

### Entry Signal
```
✓ Designated entry day (Monday by default)
✓ Positive momentum (≥1%)
✓ Adequate volatility
→ ENTER BULL CALL SPREAD
```

### Exit Signal
```
✓ Profit target hit (50%)   → EXIT
✓ Stop loss hit (75%)        → EXIT
✓ Hold period expired (7d)   → EXIT
```

## Expected Performance Characteristics

| Metric | Typical Range |
|--------|---------------|
| Win Rate | 50-65% |
| Profit Factor | 1.2-2.0 |
| Avg Win/Loss Ratio | 0.8-1.5 |
| Max Drawdown | 15-25% |

## Integration with Your System

The strategy seamlessly integrates with your existing backtesting system:

✅ Uses your MongoDB options data (NSEFO format)
✅ Works with backtest_engine.py
✅ Tracks detailed position information
✅ Logs all trades with entry/exit details
✅ Calculates comprehensive performance metrics
✅ Appears automatically in UI strategy dropdown

## Database Compatibility

Works with your options data format:
```
NSEFO-#NIFTY20201231CE1250000
         └─ Date    └─Type └─Strike
         YYYYMMDD   CE/PE  (×100)
```

## Trade Tracking

Each trade logs:
- Entry date, spot price, ATM strike
- Both leg details (BUY call, SELL call)
- Strike prices and premiums
- Exit date, reason (time/profit/loss)
- Final P&L and percentage return

## Risk Management

Built-in risk controls:
- **Position Sizing**: Uses 95% of available cash
- **Stop Loss**: Automatic exit at 75% loss
- **Profit Target**: Take profits at 50% gain
- **Time Limit**: Maximum 7 days holding period
- **Entry Filter**: Requires bullish momentum + volatility

## Next Steps

1. **Test the Strategy**:
   ```bash
   python test_bull_call_spread.py
   ```

2. **Review Results**: Check win rate, profit factor, drawdown

3. **Optimize Parameters**: Adjust strike_spacing, profit targets

4. **Compare with Other Strategies**: Run against long calls, straddles

5. **Paper Trade**: Test with real-time data before live trading

## Advanced Customization

Want to modify the strategy? Key areas to customize:

### Strike Selection
```python
# In build_bull_call_spread() method
lower_strike = atm_strike - 50    # Slightly ITM instead of ATM
higher_strike = lower_strike + 150  # Wider spread
```

### Entry Filters
```python
# In generate_signal() method
is_bullish = momentum >= 0.02  # Require 2% momentum
has_volatility = vol_ratio >= 1.5  # Higher volatility requirement
```

### Dynamic Position Sizing
```python
# Based on confidence level
confidence = momentum / momentum_threshold
position_size = base_size * min(confidence, 2.0)  # Max 2x size
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No trades executed | Lower momentum_threshold to 0.005 or volatility_threshold to 0.8 |
| All trades stopped out | Reduce stop_loss_pct to 0.50 or increase strike_spacing |
| Low win rate (<40%) | Increase momentum_threshold to 0.02 for stronger signals |
| Profits too small | Increase strike_spacing to 150 or 200 |

## Performance Comparison

Compare bull call spread vs. other strategies:

| Strategy | Risk | Reward | Cost | Complexity |
|----------|------|--------|------|------------|
| Bull Call Spread | Low (Debit) | Limited | Moderate | Medium |
| Long Call | Low (Premium) | Unlimited | High | Low |
| Long Straddle | Low (Debit) | Unlimited | Very High | Medium |
| Short Put | High | Limited | Credit | Medium |

## Support

For detailed documentation, see: [BULL_CALL_SPREAD_GUIDE.md](BULL_CALL_SPREAD_GUIDE.md)

For implementation details, see: [strategies/bull_call_spread.py](strategies/bull_call_spread.py)

---

**Status**: ✅ Fully Implemented and Ready for Testing
**Version**: 1.0
**Last Updated**: 2025-12-29
