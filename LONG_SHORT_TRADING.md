# Long & Short Trading Support

## Overview
The backtest engine now supports both **LONG** and **SHORT** trading strategies. Strategies can generate signals for opening and closing both long and short positions.

## Trading Signals

### Long Trading
- **BUY_LONG** or **BUY**: Open a long position (buy first, sell later at higher price)
- **SELL_LONG** or **SELL**: Close a long position (sell to exit)

### Short Trading
- **SELL_SHORT**: Open a short position (sell first, buy later at lower price)
- **BUY_SHORT**: Close a short position (buy to cover)

## Strategy Implementation

### Example: Moving Average Strategy with Long & Short

```python
class Strategy:
    def __init__(self, short_window=20, long_window=50, enable_short=True):
        self.short_window = short_window
        self.long_window = long_window
        self.enable_short = enable_short
        self.position = None  # 'LONG', 'SHORT', or None
    
    def generate_signal(self, current_bar, historical_data):
        # Calculate indicators
        short_ma = calculate_short_ma()
        long_ma = calculate_long_ma()
        
        # Bullish crossover
        if short_ma > long_ma:
            if self.position == 'SHORT':
                return 'BUY_SHORT'  # Close short
            elif self.position != 'LONG':
                return 'BUY_LONG'    # Open long
        
        # Bearish crossover
        elif short_ma < long_ma:
            if self.position == 'LONG':
                return 'SELL_LONG'   # Close long
            elif self.enable_short and self.position != 'SHORT':
                return 'SELL_SHORT'  # Open short
        
        return 'HOLD'
```

## UI Enhancements

### Summary Widget
- **Total Trades**: All trades (entries and exits)
- **Long Trades**: Count of long position trades
- **Short Trades**: Count of short position trades
- **Winning/Losing Trades**: Profitable vs unprofitable closed positions

### Trade Results Table
- New **Type** column shows LONG or SHORT
- Color coding:
  - 🟢 Green: BUY_LONG actions
  - 🔴 Red: SELL_LONG actions
  - 🟠 Orange: SELL_SHORT actions
  - 🟣 Purple: BUY_SHORT actions

### Interactive Chart
- **Trade Markers**:
  - 🟢 Green Arrow Up: LONG entry (₹price)
  - 🔴 Red Arrow Down: EXIT LONG (₹price)
  - 🟠 Orange Arrow Down: SHORT entry (₹price)
  - 🟣 Purple Arrow Up: COVER short (₹price)
- **Trades List Panel**:
  - Shows all trades with Type column
  - Color-coded by action type
  - Sortable by any column

## P&L Calculation

### Long Trades
- **Entry**: Buy at price A
- **Exit**: Sell at price B
- **P&L**: (B - A) × shares - total_brokerage
- **Profitable when**: Price goes UP

### Short Trades
- **Entry**: Sell short at price A
- **Exit**: Buy to cover at price B
- **P&L**: (A - B) × shares - total_brokerage
- **Profitable when**: Price goes DOWN

## Brokerage Calculation
- Entry brokerage: 0.007% of entry value
- Exit brokerage: 0.007% of exit value
- Total brokerage: Entry + Exit brokerage (deducted from P&L)

## Migrating Existing Strategies

To enable short trading in your existing strategies:

1. Add `enable_short` parameter to `__init__`
2. Track position state: `self.position = None` (or 'LONG' or 'SHORT')
3. Return appropriate signals:
   - Replace `'BUY'` with `'BUY_LONG'`
   - Replace `'SELL'` with `'SELL_LONG'`
   - Add short logic with `'SELL_SHORT'` and `'BUY_SHORT'`
4. Close existing positions before opening opposite direction

## Backward Compatibility

Old strategies using `'BUY'` and `'SELL'` signals still work:
- `'BUY'` is treated as `'BUY_LONG'`
- `'SELL'` is treated as `'SELL_LONG'`
- Only long trades will be executed (no short trades)

## Updated Strategies

The following strategies have been updated to support long & short trading:
- ✅ moving_average.py

To update other strategies, follow the pattern in moving_average.py.
