# NIFTY Options Strategy Backtesting Guide

## Overview

Your app now supports detailed options strategy backtesting with full tracking of:
- **Strike prices** used in each trade
- **Option types** (Call/Put - CE/PE)
- **Position sides** (Buy/Sell)
- **Entry and exit reasons**
- **Premium calculations**

## Available Strategies

### 1. **nifty_options_straddle.py**
Advanced options strategy simulator that tracks exact strikes and option types.

**Strategy Types:**
- **LONG_STRADDLE**: Buy ATM Call + ATM Put (profits from big moves)
- **IRON_CONDOR**: Sell OTM options, buy further OTM for protection (profits from range-bound)

## How to Use

### Step 1: Select NIFTY Data
1. In the app sidebar, search for NIFTY instruments
2. Use the filter buttons to show only:
   - **FUT** (Futures) - Orange badge
   - **OPT** (Options) - Purple badge
3. Select a NIFTY future or spot equivalent for backtesting

### Step 2: Load Options Strategy
1. Click "Add Strategy" or select from dropdown
2. Choose **nifty_options_straddle.py**
3. Strategy will load with default parameters

### Step 3: Configure Parameters

The strategy accepts these parameters:

```python
strategy_type='LONG_STRADDLE'    # or 'IRON_CONDOR'
entry_day=0                       # 0=Monday, 1=Tuesday, ..., 4=Friday
hold_days=4                       # Days to hold (Monday to Friday = 4)
atr_period=14                     # ATR calculation period
volatility_threshold=1.2          # Min volatility ratio for entry
profit_target_pct=0.50           # Exit at 50% profit
stop_loss_pct=0.75               # Exit at 75% loss
strike_step=50                    # NIFTY strike interval
lot_size=50                       # NIFTY lot size
```

### Step 4: Run Backtest
1. Set date range (e.g., 2023-01-01 to 2024-12-31)
2. Click "Run Backtest"
3. Watch console output for detailed trade logs

## Understanding the Results

### Console Output
During backtest, you'll see detailed logs like:

```
==============================================================
Position ID: 1 | Strategy: LONG_STRADDLE
Entry Date: 2023-01-02 | Spot: 18500.00
==============================================================
Strike     Type   Side   Premium     
--------------------------------------------------------------
18500      CE     BUY    250.50
18500      PE     BUY    240.75
==============================================================
Net Debit: ₹24,562.50
Volatility Ratio: 1.35
ATR: 185.50
```

### Results Table
The **Options Info** column shows:
- Strike prices
- CE (Call) or PE (Put)
- BUY or SELL side
- Exit reason in parentheses

Example: `18500 CE BUY | 18500 PE BUY (Profit target hit: 52.3%)`

### Trade Summary
After backtest completes, call `strategy.get_trade_summary()` to see:
- Total trades executed
- Win rate
- Average P&L per trade
- Detailed breakdown by position

## Strategy Logic Explained

### Long Straddle
- **Entry**: Monday when volatility ratio > threshold
- **Position**: Buy ATM Call + Buy ATM Put
- **Cost**: Total premium paid (debit)
- **Profit**: When price moves significantly in either direction
- **Exit**: Profit target, stop loss, or end of week

### Iron Condor
- **Entry**: Monday when volatility ratio < threshold
- **Position**: 
  - Sell OTM Call + Buy further OTM Call
  - Sell OTM Put + Buy further OTM Put
- **Credit**: Net premium received
- **Profit**: When price stays within range
- **Exit**: Profit target, stop loss, or end of week

## Strike Selection

### Long Straddle
- **Calls & Puts**: ATM (At The Money)
- Example: If NIFTY @ 18,525 → Strike 18,500

### Iron Condor
- **Short positions**: 1.5 × ATR away from spot
- **Long positions**: 2 strikes further out (protection)
- Example: 
  - Spot: 18,500, ATR: 200
  - Short Call: 18,800 (18,500 + 300)
  - Long Call: 18,900 (18,800 + 100)
  - Short Put: 18,200 (18,500 - 300)
  - Long Put: 18,100 (18,200 - 100)

## Premium Calculation

The strategy uses a simplified premium model:
- **Intrinsic Value**: max(0, Spot - Strike) for calls
- **Time Value**: Based on ATR and days to expiry
- **Moneyness Adjustment**: Decays exponentially with distance from spot

*Note: This is a simulation model. Real premiums may differ based on IV, Greeks, etc.*

## Tips for Better Results

1. **Use NIFTY Futures Data**: More liquid than individual options
2. **Test Different Volatility Thresholds**: 1.2-1.5 for straddles, 0.8-1.0 for condors
3. **Adjust Hold Days**: Match actual expiry cycles (weekly/monthly)
4. **Monitor Console Output**: Shows exact strikes and premiums used
5. **Compare Multiple Parameters**: Run backtests with different settings

## Example Workflow

```python
# 1. Load NIFTY future data (e.g., "NSEFO:NIFTY23DEC21500FUT")
# 2. Select nifty_options_straddle strategy
# 3. Set parameters in strategy file:

strategy = Strategy(
    strategy_type='LONG_STRADDLE',  # or 'IRON_CONDOR'
    entry_day=0,                     # Monday
    hold_days=4,                     # Hold until Friday
    profit_target_pct=0.50,          # Exit at 50% profit
    stop_loss_pct=0.75               # Exit at 75% loss
)

# 4. Run backtest for 1 year
# 5. Check "Options Info" column in results
# 6. Review console for detailed strike/premium info
```

## Interpreting Options Info

The **Options Info** column uses this format:
```
[Strike] [Type] [Side] | [Strike] [Type] [Side] (Exit Reason)
```

Examples:
- `18500 CE BUY | 18500 PE BUY (Profit target hit: 52.3%)`
  - Bought 18500 Call and Put, exited with 52.3% profit

- `18800 CE SELL | 18900 CE BUY | 18200 PE SELL | 18100 PE BUY (Hold period ended)`
  - Iron Condor: sold 18800 call, bought 18900 call protection
  - Sold 18200 put, bought 18100 put protection
  - Exited after holding period

## Advanced Features

### Custom Exit Conditions
Modify `generate_signal()` to add:
- Time-of-day exits (e.g., 3:15 PM)
- IV-based exits
- Delta-based adjustments

### Position Greeks Tracking
Add methods to calculate and track:
- Delta (directional exposure)
- Gamma (delta sensitivity)
- Theta (time decay)
- Vega (volatility sensitivity)

### Multi-leg Strategies
Extend the framework to support:
- Butterflies
- Ratio spreads
- Calendar spreads
- Custom combinations

## Troubleshooting

**Issue**: "No trades executed"
- Check volatility_threshold - may be too high/low
- Verify entry_day matches available data
- Ensure date range includes enough Mondays

**Issue**: "Premium values seem off"
- This is a simplified model for simulation
- Adjust ATR period for better time value estimates
- Real premiums require implied volatility data

**Issue**: "Can't see options info in results"
- Ensure using nifty_options_straddle.py strategy
- Check that strategy has options_legs attribute
- Verify backtest engine version is updated

## Next Steps

1. **Add Real Options Data**: Load actual CE/PE chains from database
2. **Implement IV Calculation**: Use Black-Scholes with market data
3. **Add Greeks Display**: Show delta, gamma, theta, vega for each leg
4. **Multi-Strike Analysis**: Backtest multiple strike selections simultaneously
5. **Risk Metrics**: Add max loss, margin requirements, probability of profit

---

**Questions?** The strategy prints detailed information to console during execution. Monitor it to understand exactly which strikes are being traded and why positions are being entered/exited.
