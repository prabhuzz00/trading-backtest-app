# Bull Call Spread Options Strategy

## Overview

The **Bull Call Spread** is a popular limited-risk, limited-reward options strategy designed for moderately bullish market conditions. This strategy is implemented in the trading backtest application to allow traders to test bullish options strategies with defined risk parameters.

## Strategy Structure

### Position Components
1. **BUY 1 Call Option** at a lower strike price (ITM or ATM)
   - This is the long leg
   - Pays a premium
   - Provides the bullish exposure

2. **SELL 1 Call Option** at a higher strike price (OTM)
   - This is the short leg
   - Receives a premium
   - Caps the maximum profit but reduces net cost

### Key Characteristics

| Characteristic | Description |
|---|---|
| **Market Outlook** | Moderately Bullish |
| **Risk Profile** | Limited Risk (Net Debit Paid) |
| **Reward Profile** | Limited Reward (Spread Width - Net Debit) |
| **Net Position** | Debit Spread (Pay to Enter) |
| **Breakeven** | Lower Strike + Net Debit Paid |

## Example

### Setup
- Current NIFTY Price: 17,500
- Lower Strike (BUY): 17,500 CE (ATM)
- Higher Strike (SELL): 17,600 CE (OTM, 100 points higher)

### Premium Example
- BUY 17,500 CE @ ₹150 (paid)
- SELL 17,600 CE @ ₹80 (received)
- **Net Debit = ₹150 - ₹80 = ₹70**

### Profit & Loss Scenarios

#### Maximum Profit
- Occurs when NIFTY closes **above** 17,600 at expiry
- Max Profit = (Higher Strike - Lower Strike) - Net Debit
- Max Profit = (17,600 - 17,500) - 70 = **₹30 per lot**
- For 50 lot size: **₹1,500 profit**

#### Maximum Loss
- Occurs when NIFTY closes **below** 17,500 at expiry
- Max Loss = Net Debit Paid = **₹70 per lot**
- For 50 lot size: **₹3,500 loss**

#### Breakeven Point
- Breakeven = Lower Strike + Net Debit
- Breakeven = 17,500 + 70 = **17,570**

### Payoff at Different Prices

| NIFTY at Expiry | Long Call Value | Short Call Value | Net P&L |
|---|---|---|---|
| 17,400 | 0 | 0 | -70 (Max Loss) |
| 17,500 | 0 | 0 | -70 (Max Loss) |
| 17,570 | 70 | 0 | 0 (Breakeven) |
| 17,600 | 100 | 0 | +30 (Max Profit) |
| 17,700 | 200 | -100 | +30 (Max Profit) |

## Strategy Parameters

The strategy is highly configurable with the following parameters:

```python
Strategy(
    entry_day=0,              # 0=Monday, 4=Friday - Day to enter trades
    hold_days=7,              # Days to hold position before expiry
    atr_period=14,            # Period for ATR volatility calculation
    volatility_threshold=1.0, # Minimum volatility ratio for entry
    strike_spacing=100,       # Points between long and short strikes
    profit_target_pct=0.50,   # Exit at 50% profit
    stop_loss_pct=0.75,       # Exit at 75% loss
    strike_step=50,           # Strike price rounding step
    lot_size=50,              # Contract lot size (NIFTY = 50)
    momentum_lookback=5,      # Days for momentum calculation
    momentum_threshold=0.01   # Minimum 1% upward momentum for entry
)
```

### Parameter Descriptions

| Parameter | Default | Description |
|---|---|---|
| `entry_day` | 0 (Monday) | Day of week to enter positions |
| `hold_days` | 7 | Number of days to hold before expiration |
| `atr_period` | 14 | Period for Average True Range calculation |
| `volatility_threshold` | 1.0 | Minimum volatility ratio vs. historical average |
| `strike_spacing` | 100 | Points between BUY and SELL strikes |
| `profit_target_pct` | 0.50 | Exit when 50% profit achieved |
| `stop_loss_pct` | 0.75 | Exit when 75% loss incurred |
| `strike_step` | 50 | Strike rounding increment (NIFTY = 50) |
| `lot_size` | 50 | Contract multiplier (NIFTY = 50) |
| `momentum_lookback` | 5 | Days to measure price momentum |
| `momentum_threshold` | 0.01 | Minimum 1% upward momentum required |

## Entry Conditions

The strategy enters a bull call spread position when **ALL** of the following conditions are met:

1. **Day of Week**: Current day matches `entry_day` parameter
2. **No Existing Position**: Strategy is not already in a position
3. **Bullish Momentum**: Price momentum over `momentum_lookback` days ≥ `momentum_threshold`
4. **Adequate Volatility**: Current ATR ratio ≥ `volatility_threshold`

### Entry Logic Flow
```
Is it the designated entry day?
    └─> YES
        └─> Is momentum positive (≥ 1%)?
            └─> YES
                └─> Is volatility adequate?
                    └─> YES → **ENTER BULL CALL SPREAD**
```

## Exit Conditions

The strategy exits the position when **ANY** of the following occurs:

1. **Time Expiry**: Position held for `hold_days` days
2. **Profit Target**: P&L reaches `profit_target_pct` (50% default)
3. **Stop Loss**: P&L falls to `-stop_loss_pct` (75% loss default)

### Exit Logic Flow
```
Check exit conditions:
    Days held ≥ hold_days? → EXIT (Time expired)
    P&L ≥ +50%? → EXIT (Profit target)
    P&L ≤ -75%? → EXIT (Stop loss)
```

## Option Premium Estimation

Since this is a backtesting system, option premiums are estimated using a simplified model:

```python
premium = intrinsic_value + time_value
```

Where:
- **Intrinsic Value** = max(0, Spot - Strike) for calls
- **Time Value** = ATR × sqrt(days_to_expiry / 5) × exp(-moneyness × 2)
- **Moneyness** = |Spot - Strike| / Spot

This approximation uses ATR (Average True Range) as a proxy for implied volatility.

## Database Integration

The strategy works with NIFTY options data stored in MongoDB with the naming format:

```
NSEFO-#NIFTY[YYYYMMDD][CE/PE][STRIKE]
```

Example:
- `NSEFO-#NIFTY20201231CE1250000` → NIFTY Call expiring Dec 31, 2020, Strike 12500.00

### Options Data Format
- **CE** = Call European
- **PE** = Put European
- **Strike** = Strike price × 100 (e.g., 1250000 = 12500.00)

## Usage

### Running a Backtest

```python
from engine.backtest_engine import BacktestEngine

# Initialize engine
engine = BacktestEngine(initial_cash=100000, brokerage_rate=0.00007)

# Run backtest
results = engine.run_backtest(
    strategy_path="strategies/bull_call_spread.py",
    stock_symbol="NSEFO-#NIFTY",
    start_date="2020-01-01",
    end_date="2020-12-31"
)

# View results
print(f"Total Return: {results['metrics']['total_return']:.2f}%")
print(f"Win Rate: {results['metrics']['win_rate']:.2f}%")
print(f"Max Drawdown: {results['metrics']['max_drawdown']:.2f}%")
```

### Using the Test Script

A dedicated test script is provided:

```bash
python test_bull_call_spread.py
```

This will:
- Run the strategy against NIFTY data
- Display performance metrics
- Show detailed trade information
- Print entry/exit details for each position

## Strategy Advantages

✅ **Limited Risk**: Maximum loss is capped at net debit paid
✅ **Lower Cost**: Short call reduces the net cost vs. buying calls alone
✅ **Defined Profit**: Know maximum profit upfront
✅ **Suitable for Moderate Bullishness**: Don't need explosive moves to profit
✅ **Time Decay Benefit**: If stock rises, time decay helps (short call decays faster)

## Strategy Disadvantages

❌ **Limited Profit**: Maximum gain is capped
❌ **Two Commissions**: Pay brokerage on both legs
❌ **Requires Price Movement**: Stock must move up to be profitable
❌ **Time Decay Risk**: If stock doesn't move, both options lose value

## When to Use Bull Call Spread

### Ideal Conditions
- ✅ Moderately bullish on underlying (expect 5-10% move up)
- ✅ High implied volatility (expensive options) → short leg helps offset cost
- ✅ Clear resistance level (use as higher strike)
- ✅ Defined time horizon (earnings, events)

### Avoid When
- ❌ Expecting explosive moves (unlimited upside is capped)
- ❌ Very low implied volatility (better to buy calls outright)
- ❌ Uncertain about direction
- ❌ Very short time to expiry (risk of total loss increases)

## Comparison with Other Strategies

| Strategy | Risk | Reward | Cost | Best When |
|---|---|---|---|---|
| **Bull Call Spread** | Limited | Limited | Moderate (Debit) | Moderately Bullish |
| Long Call | Limited | Unlimited | High (Debit) | Very Bullish |
| Short Put | High | Limited | Credit | Neutral to Bullish |
| Long Straddle | Limited | Unlimited | High (Debit) | High Volatility Expected |

## Greeks Profile

Understanding how Greeks affect the bull call spread:

| Greek | Impact | Description |
|---|---|---|
| **Delta** | Net Positive | Position gains as underlying rises |
| **Gamma** | Moderate | Rate of delta change is moderate |
| **Theta** | Mixed | Time decay hurts long call, helps short call |
| **Vega** | Small Negative | IV decrease slightly hurts the spread |

## Performance Optimization Tips

1. **Strike Selection**
   - Narrower spreads (50-100 pts): Lower cost, lower profit
   - Wider spreads (150-200 pts): Higher cost, higher profit potential

2. **Entry Timing**
   - Enter when momentum confirms bullish bias
   - Use technical support levels for lower strike
   - Use technical resistance for higher strike

3. **Exit Management**
   - Consider taking profits at 50% of max profit (common practice)
   - Don't let winners turn into losers
   - Exit early if underlying shows signs of reversal

4. **Parameter Tuning**
   ```python
   # Aggressive (Higher Risk/Reward)
   strike_spacing=150
   profit_target_pct=0.70
   stop_loss_pct=0.90
   
   # Conservative (Lower Risk/Reward)
   strike_spacing=50
   profit_target_pct=0.40
   stop_loss_pct=0.60
   ```

## Monitoring and Analysis

### Key Metrics to Track
- **Win Rate**: Should be >50% for profitable strategy
- **Profit Factor**: Total wins / Total losses > 1.5 recommended
- **Average Win vs. Loss**: Aim for avg_win ≥ avg_loss
- **Max Drawdown**: Keep under 20-30% for options strategies

### Trade Log Analysis
Each trade logs detailed information:
- Entry date and spot price
- Strike prices for both legs
- Premiums paid/received
- Exit date and reason
- Final P&L and percentage

## Technical Implementation

### Core Methods

```python
def build_bull_call_spread(self, spot, atr, days_to_expiry):
    """
    Constructs the two-leg spread:
    1. BUY call at ATM or slightly ITM
    2. SELL call at OTM (spot + strike_spacing)
    
    Returns:
        - legs: List of option legs with details
        - net_debit: Cost of the spread
        - max_profit: Maximum possible profit
        - max_loss: Maximum possible loss (= net_debit)
    """
```

```python
def calculate_position_value(self, legs, current_spot, current_atr, days_remaining):
    """
    Calculates current mark-to-market value:
    - Updates premiums based on current spot and volatility
    - Computes net position value
    - Used for P&L and exit decision tracking
    """
```

## Troubleshooting

### Issue: No Trades Executed
- Check if entry_day matches data days
- Verify momentum_threshold isn't too high
- Ensure volatility_threshold is reasonable (try 0.8-1.0)

### Issue: All Trades Stopped Out
- Reduce stop_loss_pct (make it less aggressive)
- Increase strike_spacing for more profit potential
- Check if entry momentum threshold is too low (entering weak trends)

### Issue: Low Win Rate
- Tighten momentum_threshold (ensure stronger bullish signal)
- Consider increasing hold_days (give more time to develop)
- Review exit parameters (profit_target might be too ambitious)

## Further Enhancements

Possible improvements for production use:

1. **Real Option Data**: Replace estimated premiums with actual option prices from database
2. **IV-based Entry**: Add implied volatility filtering
3. **Dynamic Strike Selection**: Use technical levels for strike placement
4. **Risk Management**: Add position sizing based on portfolio risk
5. **Greeks Tracking**: Monitor delta, gamma, theta in real-time
6. **Adjustment Strategies**: Roll up/down strikes if underlying moves significantly

## References

- [Options Strategies Guide](https://www.optionsplaybook.com/option-strategies/bull-call-spread/)
- NIFTY Options: Lot Size = 50, Strike Step = 50 points
- Brokerage: ₹7,000 per ₹1 crore (0.007%)

---

## Contact & Support

For issues or questions about the bull call spread strategy implementation, please refer to the main README.md or raise an issue in the project repository.

**Strategy File**: `strategies/bull_call_spread.py`  
**Test Script**: `test_bull_call_spread.py`  
**Documentation**: `BULL_CALL_SPREAD_GUIDE.md` (this file)
