# Quick Start Guide - Options Strategy Backtesting

## ✅ All Issues Fixed!

The syntax errors have been resolved and all features are now working correctly.

## What Was Fixed

1. **Removed stray period (`.`) on line 24** in stock_sidebar.py
2. **Fixed docstring typo** (removed `0` prefix)
3. **Verified all imports and functions** work correctly
4. **Tested all new features** - all passing ✓

## How to Use the New Features

### 1. Start the App
```bash
python src/main.py
```

### 2. Load Instruments
- The sidebar now shows **ALL** instruments by default
- Use filter buttons to show specific types:
  - **All** - All instruments (gray)
  - **Stocks** - Equity instruments (blue badge)
  - **Futures** - NSEFO futures (orange badge)
  - **Options** - CE/PE options (purple badge)

### 3. Select NIFTY Data
- Search for "NIFTY" in the sidebar
- Click on any NIFTY future or spot instrument
- Example: `NSEFO:NIFTY23DEC21500FUT`

### 4. Run Options Strategy
1. Click **"Add Strategy"** or select from dropdown
2. Choose **`nifty_options_straddle.py`**
3. Set date range (e.g., 2023-01-01 to 2024-12-31)
4. Click **"Run Backtest"**

### 5. View Results

#### Console Output
Watch for detailed logs like:
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
```

#### Results Table
Check the **"Options Info"** column:
- Shows exact strikes: `18500 CE BUY | 18500 PE BUY`
- Exit reasons: `(Profit target hit: 52.3%)`

## Strategy Parameters

Edit in `strategies/nifty_options_straddle.py`:

```python
strategy_type='LONG_STRADDLE'    # or 'IRON_CONDOR'
entry_day=0                       # 0=Monday, 4=Friday
hold_days=4                       # Days to hold
profit_target_pct=0.50           # 50% profit exit
stop_loss_pct=0.75               # 75% loss exit
strike_step=50                    # NIFTY strike interval
lot_size=50                       # NIFTY lot size
```

## Features Now Available

✓ **Futures & Options loading** from database (NSEFO collections)
✓ **Color-coded badges** by instrument type
✓ **Filter buttons** to show specific instrument types
✓ **Strike price tracking** in options strategies
✓ **CE/PE side tracking** (Call/Put identification)
✓ **Entry/exit reason logging** in console and results
✓ **Options Info column** in results table
✓ **Detailed trade summaries** with strike details

## Testing Your Setup

Run the test script to verify everything works:
```bash
python test_options_features.py
```

Should show:
```
✓ All tests passed! Features are working correctly.
```

## Next Steps

1. **Load your NIFTY data** from MongoDB
2. **Experiment with parameters** in the strategy file
3. **Compare LONG_STRADDLE vs IRON_CONDOR** performance
4. **Check console output** for detailed strike information
5. **Review OPTIONS_STRATEGY_GUIDE.md** for advanced usage

## Troubleshooting

**Issue**: No instruments loading
- Check MongoDB connection in `config/config.yaml`
- Verify NSEFO collections exist in database

**Issue**: Strategy not showing strikes
- Ensure using `nifty_options_straddle.py` (not `weekly_straddle.py`)
- Check console output during backtest

**Issue**: App won't start
- Run: `python test_options_features.py`
- Check for any error messages

---

**Status**: 🟢 All systems operational!

The app is now ready to backtest NIFTY options strategies with full strike and side tracking.
