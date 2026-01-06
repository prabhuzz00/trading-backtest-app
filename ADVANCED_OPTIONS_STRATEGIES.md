# Nifty 50 Advanced Options Strategies - Implementation Complete

Successfully implemented 6 advanced options strategies for Nifty 50 options trading.

## Implemented Strategies

### 1. Short Vol Inventory (Strike Grid) - `short_vol_inventory.py`
**Type:** Short Volatility / Premium Collection  
**Structure:** Sells multiple OTM options across a grid of strikes  
**Best For:** Range-bound markets, low volatility environments  

**Key Features:**
- Systematic premium collection across multiple strikes
- Configurable number of strikes and spacing
- Optional both-sides (calls + puts) or one-side only
- Aggregate delta monitoring
- Profit target: 60% of max profit (default)

**Parameters:**
- `num_strikes`: Number of strikes in grid (default: 5)
- `strike_spacing_pct`: Spacing between strikes (default: 2%)
- `sell_both_sides`: Sell both calls and puts (default: True)
- `max_aggregate_delta`: Maximum net delta (default: 0.5)

---

### 2. Short Put Ladder/Strip - `short_put_ladder.py`
**Type:** Short Premium / Ratio Strategy  
**Structure:** Sells multiple puts with increasing size at lower strikes  
**Best For:** Neutral to slightly bearish markets  

**Key Features:**
- Ratio structure (more contracts at lower strikes)
- Example: 1x at highest, 1.5x at middle, 2.25x at lowest
- Collects premium with increasing exposure downward
- Profit target: 60% of max profit (default)

**Parameters:**
- `num_strikes`: Number of put strikes (default: 3)
- `strike_spacing_pct`: Spacing between strikes (default: 3%)
- `ratio_multiplier`: Contract multiplier per level (default: 1.5)
- `base_delta`: Target delta for highest strike (default: 0.30)

---

### 3. Tail Wing Hedge - `tail_wing_hedge.py`
**Type:** Tail Risk Protection / Asymmetric Hedge  
**Structure:** Buys far OTM puts, sells near-ATM puts to finance  
**Best For:** Portfolio insurance, tail risk protection  

**Key Features:**
- Low-cost or zero-cost hedge structure
- Provides protection against market crashes
- Wing structure finances the tail hedge
- Profit multiplier: 3x on tail events (default)

**Parameters:**
- `tail_strike_pct`: Distance below spot for tail hedge (default: 10%)
- `wing_strike_pct`: Distance below spot for wing (default: 3%)
- `wing_ratio`: Ratio of wings to tail hedge (default: 2.0)
- `max_debit_pct`: Maximum net debit (default: 0.5% of spot)

---

### 4. Risk-Defined Short Premium Band - `risk_defined_premium_band.py`
**Type:** Iron Condor Variant / Range Strategy  
**Structure:** Sells OTM call spread + OTM put spread  
**Best For:** Range-bound, low volatility markets  

**Key Features:**
- Fully defined risk on both sides
- Creates a profitable "band" or range
- Max loss = spread width minus premium
- Profit target: 50% of max profit (default)

**Parameters:**
- `band_width_pct`: Width of profitable band (default: 10%)
- `spread_width_pct`: Width of each spread (default: 2%)
- `target_delta`: Target delta for short strikes (default: 0.20)

---

### 5. Bullish Risk Reversal - `bullish_risk_reversal.py`
**Type:** Directional / Synthetic Long  
**Structure:** Buys OTM call, sells OTM put  
**Best For:** Bullish directional trades  

**Key Features:**
- Synthetic long position with defined downside
- Low cost or credit structure
- Unlimited upside potential
- Requires positive momentum to enter
- Profit target: 100% (default)

**Parameters:**
- `call_otm_pct`: Distance above spot for call (default: 5%)
- `put_otm_pct`: Distance below spot for put (default: 5%)
- `max_debit_pct`: Maximum net debit (default: 1% of spot)
- `momentum_lookback`: Momentum period (default: 10 days)

---

### 6. Bullish Carry + Call Backspread - `bullish_carry_call_backspread.py`
**Type:** Income + Unlimited Upside  
**Structure:** Sells 1x ATM call, buys 2x OTM calls  
**Best For:** Bullish markets expecting volatility  

**Key Features:**
- Collects premium (carry component)
- Unlimited upside from backspread
- Danger zone between strikes (max loss area)
- Requires positive momentum to enter
- Profit target: 200% (default)

**Parameters:**
- `short_call_otm_pct`: Distance above spot for short call (default: 2%)
- `long_call_otm_pct`: Distance above spot for long calls (default: 5%)
- `backspread_ratio`: Ratio of long to short (default: 2.0)
- `momentum_threshold`: Minimum momentum (default: 1%)

---

## Common Features Across All Strategies

### 1. Database Integration
- Fetches actual option premiums from MongoDB
- Falls back to theoretical pricing if data unavailable
- Uses Black-Scholes approximations with volatility adjustments

### 2. Risk Management
- Configurable profit targets and stop losses
- Time-based exits (default: 7-14 days)
- Position-specific exit rules
- Detailed trade logging

### 3. Strike Selection
- Automatic strike rounding to exchange standards
- Strike step: 50 points (5000 paise) default
- Dynamic strike calculation based on spot price

### 4. Expiry Management
- Uses weekly expiries (Thursdays)
- Configurable min/max days to expiry
- Automatic expiry date calculation

### 5. Position Tracking
- Detailed leg-by-leg tracking
- Real-time P&L calculation
- Delta monitoring
- Position ID for trade tracking

---

## Testing the Strategies

### Basic Test Structure
```python
from strategies.short_vol_inventory import Strategy as ShortVolInventory
from src.engine.backtest_engine import BacktestEngine

# Initialize strategy
strategy = ShortVolInventory(
    entry_day=None,  # Any day for testing
    hold_days=7,
    num_strikes=5,
    strike_spacing_pct=0.02
)

# Run backtest
engine = BacktestEngine(
    strategy=strategy,
    symbol='NIFTY',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=1000000
)

results = engine.run()
```

### Key Testing Considerations

1. **Data Availability**: Ensure Nifty options data is available in MongoDB
2. **Symbol Format**: Options follow format `NSEFO:#NIFTYYYYYMMDDCE/PE<strike>`
3. **Lot Size**: Default 75 (Nifty 50 standard)
4. **Capital Requirements**: Varies by strategy complexity

---

## Strategy Selection Guide

### Choose based on market outlook:

**Neutral/Range-Bound:**
- Short Vol Inventory (Strike Grid)
- Risk-Defined Short Premium Band
- Short Put Ladder (slight bearish bias)

**Bullish:**
- Bullish Risk Reversal
- Bullish Carry + Call Backspread

**Risk Protection:**
- Tail Wing Hedge

**High IV:**
- Short Vol Inventory
- Risk-Defined Premium Band

**Low IV expecting expansion:**
- Tail Wing Hedge
- Bullish Carry + Call Backspread

---

## Next Steps

1. **Test Individual Strategies**: Start with simpler strategies (Risk-Defined Band)
2. **Validate Data**: Ensure options data is available for test periods
3. **Parameter Optimization**: Adjust parameters based on backtest results
4. **Risk Analysis**: Monitor max drawdown and risk metrics
5. **Combine Strategies**: Consider portfolio approach with multiple strategies

---

## File Locations

All strategy files are located in: `d:\project\trading-backtest-app\strategies\`

- `short_vol_inventory.py`
- `short_put_ladder.py`
- `tail_wing_hedge.py`
- `risk_defined_premium_band.py`
- `bullish_risk_reversal.py`
- `bullish_carry_call_backspread.py`

---

## Important Notes

1. **Options Data Required**: These strategies require Nifty options chain data
2. **Capital Intensive**: Options strategies can require significant margin
3. **Volatility Dependent**: Results highly dependent on IV conditions
4. **Expiry Management**: Weekly expiries require active management
5. **Greeks Monitoring**: Delta, theta, and vega are estimated - use for reference

---

## Support and Documentation

Each strategy file includes:
- Detailed docstring with strategy description
- Parameter explanations
- Risk characteristics
- Entry/exit logic
- Trade logging functionality

For questions or issues, refer to the strategy-specific docstrings or test files.
