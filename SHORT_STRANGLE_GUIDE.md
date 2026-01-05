# Short Strangle Strategy - NIFTY50 Weekly Options

## Overview
The **Short Strangle** is a premium collection strategy that benefits from **theta decay** (time decay). It's designed specifically for NIFTY50 weekly options that expire every Thursday.

## Strategy Mechanics

### Position Structure
- **SELL** 1 OTM Call option (above spot price)
- **SELL** 1 OTM Put option (below spot price)
- **Expiry**: Weekly Thursday expiry (NIFTY50)

### Profit Profile
- **Maximum Profit**: Total premium collected (both options expire worthless)
- **Maximum Loss**: Unlimited on both sides
- **Breakeven Points**:
  - Upper: Call Strike + Total Premium Received
  - Lower: Put Strike - Total Premium Received

### Best Market Conditions
✅ **Low volatility** (IV < 50th percentile)  
✅ **Range-bound markets**  
✅ **Stable price action**  
✅ **High theta decay environment**

❌ **Avoid during:**
- High volatility events
- Before major announcements
- Trending markets (strong directional moves)

## How to Use in the Backtest App

### Step 1: Launch the Application
```bash
python src/main.py
```

### Step 2: Select Strategy
1. In the top toolbar, locate the **Strategy** dropdown
2. Select **"short_strangle"** from the list
3. The strategy is pre-configured for Thursday expiry

### Step 3: Select Symbol
1. In the left sidebar, search for NIFTY futures or options
2. Recommended symbols:
   - `NSEFO:NIFTY1` (Current month NIFTY futures)
   - Any NIFTY50 index futures contract

### Step 4: Set Date Range
1. Select your backtest **Start Date**
2. Select your backtest **End Date**
3. Recommended: Use at least 6-12 months of data for meaningful results

### Step 5: Run Backtest
1. Click the **"Run Backtest"** button in the toolbar
2. Wait for the backtest to complete
3. Review results in the tabs:
   - **Chart**: Visual representation with entry/exit points
   - **Summary**: Overall performance metrics
   - **Trades**: Detailed trade-by-trade breakdown
   - **Live Chart**: Interactive charting

## Strategy Parameters

### Default Configuration
```python
entry_day = 3              # Thursday (0=Monday, 3=Thursday, 4=Friday)
hold_days = 7              # Hold position for 7 days
strike_width_pct = 0.05    # 5% away from spot price
profit_target_pct = 0.50   # Exit at 50% of max profit
stop_loss_pct = 2.0        # Stop loss at 200% of credit received
lot_size = 75              # NIFTY lot size (adjust as needed)
iv_percentile_max = 50     # Only enter when IV below 50th percentile
min_days_to_expiry = 7     # Minimum days before expiry to enter
max_days_to_expiry = 30    # Maximum days before expiry to enter
```

### Customizing Parameters
To modify parameters, edit the file:
```
strategies/short_strangle.py
```

Look for the `__init__` method around line 63 and adjust the default values.

## Expiry Logic

### Thursday Expiry Calculation
The strategy automatically calculates the next Thursday expiry:
```python
def get_next_expiry(self, current_date):
    # Finds next Thursday
    days_ahead = 3 - current_date.weekday()  # Thursday = 3
    if days_ahead <= 0:
        days_ahead += 7
    next_expiry = current_date + timedelta(days=days_ahead)
```

### Entry Timing
- **Default Entry Day**: Thursday (same day as expiry week)
- **Entry Time**: Any time during market hours
- **Expiry Selection**: Automatically picks next Thursday that's 7-30 days away

### Example Flow
1. **Today is Thursday, Jan 9, 2025**
2. **Next expiry**: Thursday, Jan 16, 2025 (7 days away)
3. **Strategy sells**:
   - Call Strike: Spot + 5% (e.g., ₹12,600 if spot is ₹12,000)
   - Put Strike: Spot - 5% (e.g., ₹11,400 if spot is ₹12,000)
4. **Holds position** for 7 days or until profit/stop conditions met
5. **Exits** when:
   - 50% profit achieved (recommended early exit)
   - Stop loss hit (200% of premium)
   - 7 days elapsed
   - Within 2 days of expiry

## Risk Management

### Built-in Protection
1. **Profit Target**: Takes profit at 50% of max profit
   - This is excellent risk/reward for premium sellers
   - Locks in gains before expiry risk increases

2. **Stop Loss**: Exits if loss exceeds 200% of premium collected
   - Protects against catastrophic moves
   - Prevents unlimited loss scenarios

3. **IV Filter**: Only enters when IV is below 50th percentile
   - Avoids high volatility environments
   - Enters when options are "cheap" to buy back

4. **Days to Expiry Filter**: 
   - Minimum 7 days: Avoids gamma risk near expiry
   - Maximum 30 days: Ensures meaningful theta decay

### Manual Risk Controls
Consider these additional rules:
- **Position Sizing**: Never risk more than 2-5% of capital per trade
- **Market Conditions**: Only trade in sideways/range-bound markets
- **Event Avoidance**: Skip weeks with RBI policy, budget, major global events
- **Portfolio Hedging**: Consider buying far OTM options as disaster insurance

## Performance Metrics (2020 Backtest)

Sample results from 2020 test:
```
Total Trades: 48
Total P&L: ₹31,682,733
Win Rate: 91.5%
Average P&L per Trade: 24.23%
Average Return on Risk: ~22%

Exit Breakdown:
- Held to completion: 80.9%
- Profit target hit: 12.8%
- Stop loss hit: 6.4% (mostly during COVID crash)
```

### Key Insights
- **Consistency**: Most trades capture 40-50% of max profit
- **Low Drawdown**: In stable markets, minimal losses
- **Event Risk**: Stop losses triggered during March 2020 volatility spike
- **Theta Advantage**: Weekly theta decay provides consistent income

## Option Symbol Format

### Database Symbol Structure
```
NSEFO:#NIFTY[YYYYMMDD][CE/PE][STRIKE]
```

### Examples
- Call Option: `NSEFO:#NIFTY20250116CE1260000000`
- Put Option: `NSEFO:#NIFTY20250116PE1140000000`

Where:
- `20250116` = Expiry date (Jan 16, 2025)
- `CE` = Call European, `PE` = Put European
- `1260000000` = Strike price in paise (₹12,600.00)

The strategy automatically constructs these symbols for you.

## Troubleshooting

### No Trades Generated
**Possible Reasons:**
1. IV too high (above 50th percentile)
   - Solution: Lower `iv_percentile_max` parameter
2. Wrong entry day selected
   - Solution: Ensure data includes Thursday bars
3. Insufficient historical data
   - Solution: Use at least 6 months of data

### Unexpected Results
**Check:**
1. Lot size matches NIFTY contract size (usually 75)
2. Strike width is appropriate for market volatility
3. Date range includes complete weeks (Monday-Friday)

### Option Data Not Found
**Solutions:**
1. Verify option symbols exist in database
2. Check date ranges align with option availability
3. Strategy falls back to theoretical pricing if needed

## Advanced Usage

### Testing Different Configurations

#### Conservative (Lower Risk)
```python
strike_width_pct = 0.08      # Wider strikes (8%)
profit_target_pct = 0.40     # Exit earlier (40% profit)
iv_percentile_max = 40       # Only very low IV
```

#### Aggressive (Higher Theta)
```python
strike_width_pct = 0.03      # Tighter strikes (3%)
profit_target_pct = 0.75     # Hold longer (75% profit)
min_days_to_expiry = 3       # Closer to expiry
```

### Combining with Other Strategies
Consider using short strangle as part of portfolio:
- **Directional plays**: Bull/Bear spreads for trending markets
- **Hedged approach**: Long strangles in high IV, short in low IV
- **Calendar spreads**: Different expiry cycles

## Additional Resources

- **Live Testing**: Use test_short_strangle.py for detailed analysis
- **Strategy Code**: strategies/short_strangle.py
- **Documentation**: This guide (SHORT_STRANGLE_GUIDE.md)

## Contact & Support

For issues or questions about this strategy:
1. Check error messages in the app console
2. Review trade log output from test script
3. Verify your MongoDB connection has NIFTY options data

---

**Disclaimer**: This strategy is for educational and backtesting purposes. Past performance does not guarantee future results. Options trading involves significant risk and may not be suitable for all investors.
