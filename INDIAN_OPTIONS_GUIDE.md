# Indian Options Market & Backtest Engine Guide

## How Options Work in Indian Market

### Basics

**Options** are derivative contracts that give the buyer the right (but not obligation) to buy or sell an underlying asset at a predetermined price (strike price) before or at expiration.

### Indian Market Specifics

1. **Style**: European (can only be exercised at expiry, not before)
2. **Settlement**: Cash-settled (no physical delivery)
3. **Underlying**: Nifty 50, Bank Nifty, stocks, etc.
4. **Lot Size**: Fixed per instrument (Nifty 50 = 75 units)
5. **Expiry**: Weekly (Thursdays) and Monthly (last Thursday)
6. **Quote**: Premium in Rupees, Strike in Rupees
7. **Tick Size**: Minimum price movement (₹0.05 for Nifty)

### Call vs Put

#### CALL Options
- **BUY CALL**: 
  - You PAY premium
  - Right to BUY underlying at strike price
  - Profit when price goes UP above (strike + premium paid)
  - Max Loss: Premium paid
  - Max Profit: Unlimited
  
- **SELL CALL (Write Call)**:
  - You RECEIVE premium
  - Obligation to SELL underlying at strike price
  - Profit when price stays BELOW strike (keep premium)
  - Max Loss: Unlimited (if price rises)
  - Max Profit: Premium received

#### PUT Options
- **BUY PUT**:
  - You PAY premium
  - Right to SELL underlying at strike price
  - Profit when price goes DOWN below (strike - premium paid)
  - Max Loss: Premium paid
  - Max Profit: Strike price (if underlying goes to 0)
  
- **SELL PUT (Write Put)**:
  - You RECEIVE premium
  - Obligation to BUY underlying at strike price
  - Profit when price stays ABOVE strike (keep premium)
  - Max Loss: Strike price (if underlying goes to 0)
  - Max Profit: Premium received

---

## Options Greeks (Risk Parameters)

### Delta (Δ)
- Rate of change of option price vs underlying price
- Ranges: Calls (0 to +1), Puts (0 to -1)
- ATM options ≈ ±0.50
- Deep ITM calls → +1.00, Deep OTM calls → 0
- Deep ITM puts → -1.00, Deep OTM puts → 0

### Gamma (Γ)
- Rate of change of delta vs underlying price
- Highest for ATM options
- Important for delta hedging

### Theta (Θ)
- Time decay - premium loss per day
- Always negative for long positions
- Always positive for short positions
- Accelerates near expiry

### Vega (ν)
- Sensitivity to volatility changes
- Positive for long options (benefit from IV increase)
- Negative for short options (hurt by IV increase)

---

## Common Options Strategies

### 1. Directional Strategies

#### Long Call
- **Setup**: Buy 1 Call
- **View**: Bullish
- **Max Loss**: Premium paid
- **Max Profit**: Unlimited
- **Best When**: Expecting strong upward move, low volatility

#### Long Put
- **Setup**: Buy 1 Put
- **View**: Bearish
- **Max Loss**: Premium paid
- **Max Profit**: Strike - premium
- **Best When**: Expecting strong downward move

#### Short Call (Naked)
- **Setup**: Sell 1 Call
- **View**: Bearish/Neutral
- **Max Loss**: Unlimited
- **Max Profit**: Premium received
- **Best When**: Expecting sideways/down move, high volatility

#### Short Put (Naked)
- **Setup**: Sell 1 Put
- **View**: Bullish/Neutral
- **Max Loss**: Strike - premium
- **Max Profit**: Premium received
- **Best When**: Expecting sideways/up move, high volatility

### 2. Spread Strategies

#### Bull Call Spread
- **Setup**: Buy lower strike call + Sell higher strike call
- **View**: Moderately bullish
- **Max Loss**: Net debit paid
- **Max Profit**: (Higher strike - Lower strike) - Net debit
- **Best When**: Expecting moderate upward move

#### Bear Put Spread
- **Setup**: Buy higher strike put + Sell lower strike put
- **View**: Moderately bearish
- **Max Loss**: Net debit paid
- **Max Profit**: (Higher strike - Lower strike) - Net debit
- **Best When**: Expecting moderate downward move

#### Bull Put Spread (Credit Spread)
- **Setup**: Sell higher strike put + Buy lower strike put
- **View**: Bullish/Neutral
- **Max Loss**: (Higher strike - Lower strike) - Net credit
- **Max Profit**: Net credit received
- **Best When**: Expecting sideways/up move

#### Bear Call Spread (Credit Spread)
- **Setup**: Sell lower strike call + Buy higher strike call
- **View**: Bearish/Neutral
- **Max Loss**: (Higher strike - Lower strike) - Net credit
- **Max Profit**: Net credit received
- **Best When**: Expecting sideways/down move

### 3. Volatility Strategies

#### Long Straddle
- **Setup**: Buy ATM call + Buy ATM put (same strike)
- **View**: High volatility expected
- **Max Loss**: Total premium paid
- **Max Profit**: Unlimited
- **Best When**: Expecting big move (either direction)

#### Short Straddle
- **Setup**: Sell ATM call + Sell ATM put (same strike)
- **View**: Low volatility expected
- **Max Loss**: Unlimited
- **Max Profit**: Total premium received
- **Best When**: Expecting no big move, range-bound

#### Long Strangle
- **Setup**: Buy OTM call + Buy OTM put (different strikes)
- **View**: High volatility expected (cheaper than straddle)
- **Max Loss**: Total premium paid
- **Max Profit**: Unlimited
- **Best When**: Expecting big move, lower cost than straddle

#### Short Strangle
- **Setup**: Sell OTM call + Sell OTM put (different strikes)
- **View**: Low volatility expected
- **Max Loss**: Unlimited
- **Max Profit**: Total premium received
- **Best When**: Expecting range-bound market

### 4. Advanced Strategies

#### Iron Condor
- **Setup**: Sell OTM put spread + Sell OTM call spread
- **View**: Neutral (very low volatility)
- **Max Loss**: Width of spread - net credit
- **Max Profit**: Net credit received
- **Best When**: Expecting tight range

#### Butterfly Spread
- **Setup**: Buy 1 lower strike + Sell 2 middle strikes + Buy 1 higher strike
- **View**: Neutral (expecting price at middle strike)
- **Max Loss**: Net debit paid
- **Max Profit**: (Middle strike - Lower strike) - Net debit
- **Best When**: Expecting price to stay at specific level

#### Calendar Spread
- **Setup**: Sell near-term option + Buy longer-term option (same strike)
- **View**: Neutral to slightly bullish/bearish
- **Max Loss**: Net debit paid
- **Max Profit**: Depends on near-term expiry value
- **Best When**: Expecting low volatility short-term, increase later

---

## Backtest Engine Architecture

### Two Engines

#### 1. Standard Backtest Engine (`backtest_engine.py`)
- For equity strategies (long/short stocks)
- Simple position tracking
- Direct P&L calculation

#### 2. Options Backtest Engine (`options_backtest_engine.py`)
- **Purpose**: Specifically designed for options strategies
- **Handles**:
  - Multi-leg positions
  - Complex P&L calculations
  - Greeks tracking
  - Time decay
  - Premium tracking

### Auto-Detection
The UI automatically detects if a strategy is an options strategy by checking for keywords:
- option, call, put, strike, premium
- spread, strangle, straddle, condor
- get_option_symbol, fetch_option_premium, options_legs

### Strategy Requirements

Options strategies must implement:

```python
class Strategy:
    def __init__(self, ...):
        self.position = None
        self.options_legs = []
        self.trade_log = []
        self.position_id = 0
        self.lot_size = 75  # Nifty standard
        
    def set_underlying_symbol(self, symbol):
        self.underlying_symbol = symbol
        
    def generate_signal(self, current_bar, historical_data):
        # Required by backtest engine
        # Returns: 'BUY', 'SELL', 'HOLD'
        pass
        
    def get_trade_log(self):
        return self.trade_log
```

### Trade Log Format

#### Entry Trade
```python
{
    'date': entry_date,
    'action': 'ENTER_XXX',  # ENTER_GRID, ENTER_SPREAD, etc.
    'spot': underlying_price,
    'credit': net_credit_received,  # For credit strategies
    'debit': net_debit_paid,        # For debit strategies
    'position_id': unique_id,
    'legs': [
        {
            'type': 'SELL_CALL' / 'BUY_CALL' / 'SELL_PUT' / 'BUY_PUT',
            'strike': strike_price,
            'premium': premium_value,
            'quantity': lot_size,
            'delta': estimated_delta
        },
        # ... more legs
    ]
}
```

#### Exit Trade
```python
{
    'date': exit_date,
    'action': 'EXIT_XXX',
    'spot': underlying_price,
    'pnl': realized_pnl,
    'pnl_pct': pnl_percentage,
    'days_held': number_of_days,
    'exit_reason': 'TIME' / 'PROFIT_TARGET' / 'STOP_LOSS',
    'position_id': unique_id,
    'closing_cost': cost_to_close_position,
    'legs': [...]  # Same format as entry
}
```

---

## P&L Calculation

### Credit Strategies (Selling Options)
- **Entry**: Receive premium (add to cash)
- **Exit**: Buy back options (deduct from cash)
- **P&L** = Premium received - Cost to buy back - Brokerage

Example: Short Strangle
```
Entry: Sell call @₹50 + Sell put @₹50 = ₹100 received
Exit: Buy call @₹20 + Buy put @₹30 = ₹50 paid
P&L = ₹100 - ₹50 = ₹50 profit (50%)
```

### Debit Strategies (Buying Options)
- **Entry**: Pay premium (deduct from cash)
- **Exit**: Sell options (add to cash)
- **P&L** = Proceeds from sale - Premium paid - Brokerage

Example: Bull Call Spread
```
Entry: Buy call @₹100 - Sell call @₹40 = ₹60 paid
Exit: Sell call @₹150 - Buy call @₹90 = ₹60 received
P&L = ₹60 - ₹60 = ₹0 breakeven (0%)
```

---

## Costs & Charges

### Brokerage
- Default: 0.01% (₹10 per ₹1 lakh)
- Applied on both entry and exit
- Total brokerage = Entry brokerage + Exit brokerage

### Slippage
- Default: 0.05% of premium
- Accounts for bid-ask spread
- Applied on premium value

### STT (Securities Transaction Tax)
- Not currently implemented (can be added)
- Typically 0.05% on sell side for options

---

## Best Practices

### 1. Position Sizing
- Never risk more than 2-5% per trade
- Account for maximum loss, not just premium
- Use lot size appropriately (Nifty = 75)

### 2. Risk Management
- Always define max loss before entry
- Use stop losses (typically 200% of credit for short strategies)
- Use profit targets (50-70% of max profit for short strategies)
- Avoid holding through expiry (gamma risk)

### 3. Timing
- **Entries**: Monday-Wednesday for weekly options
- **Avoid**: Thursday entries (expiry day - high gamma)
- **Exits**: Close at 50-75% profit or 2-3 days before expiry

### 4. Volatility Considerations
- **Sell options**: When IV is high (expensive premiums)
- **Buy options**: When IV is low (cheap premiums)
- Track IV percentile (aim for >70 to sell, <30 to buy)

### 5. Greeks Management
- **Delta**: Keep portfolio delta neutral or match market view
- **Theta**: Positive for income strategies (collect time decay)
- **Vega**: Be aware of volatility risk (especially for short options)
- **Gamma**: Watch near expiry (delta changes rapidly)

---

## Strategy Selection Guide

| Market Condition | Best Strategy | Type |
|------------------|---------------|------|
| Strong Bullish | Long Call, Bull Call Spread | Debit |
| Moderate Bullish | Bull Put Spread, Risk Reversal | Credit/Mixed |
| Range-Bound | Iron Condor, Short Strangle | Credit |
| High Volatility | Long Straddle, Long Strangle | Debit |
| Low Volatility | Short Straddle, Short Strangle | Credit |
| Strong Bearish | Long Put, Bear Put Spread | Debit |
| Moderate Bearish | Bear Call Spread | Credit |

---

## Testing Your Strategy

1. **Backtest Period**: Use at least 1 year of data
2. **Different Market Conditions**: Test in bull, bear, and sideways markets
3. **Metrics to Watch**:
   - Win rate (target: 50-70%)
   - Profit factor (target: >1.5)
   - Max drawdown (keep under 20%)
   - Sharpe ratio (target: >1.0)
4. **Adjust Parameters**: Optimize for consistent returns, not maximum returns
5. **Forward Test**: Paper trade before live

---

## Troubleshooting

### Strategy Not Entering Positions
- Check entry conditions are not too strict
- Verify options data is available in database
- Check IV calculations and thresholds
- Review momentum/trend filters

### Unrealistic P&L
- Verify strike prices are reasonable (not too far OTM)
- Check premium calculations (use real data when available)
- Ensure lot size is correct (Nifty = 75)
- Verify max profit/loss caps are applied

### High Drawdown
- Reduce position size
- Tighten stop losses
- Use more defensive strategies (spreads instead of naked)
- Increase diversification

---

For more help, see:
- `ADVANCED_OPTIONS_STRATEGIES.md` - Strategy details
- `STRATEGY_PARAMETERS_GUIDE.md` - Parameter tuning
- Test files in root directory for examples
