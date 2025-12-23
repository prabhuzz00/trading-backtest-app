# Lightweight Chart Troubleshooting Guide

## Recent Updates (December 2025)

### ✨ New Feature: Trades List Panel

The Interactive Chart now includes a **trades list panel** that displays all trades in a table format:

**Features:**
- 📊 Side-by-side view of chart and trades list
- 🔄 Toggle visibility with "Show Trades List" button
- 📋 Detailed trade information: Date, Action, Price, Quantity, Value, P&L, P&L %
- 🎨 Color-coded: Green for BUY trades, Red for SELL trades
- 💰 Profit/Loss highlighting on SELL trades
- 📏 Resizable splitter - adjust panel sizes as needed
- 🔍 Sortable columns - click headers to sort

**How to Use:**
1. Run a backtest
2. Go to the "Interactive Chart" tab
3. Click "Show Trades List" button to display the trades panel
4. Drag the splitter to resize chart vs trades list
5. Click column headers to sort trades by date, price, P&L, etc.

### 🔧 Technical Improvements

**Fixed:**
- Pinned lightweight-charts library to version 4.1.0 for stability
- Added trades list table with QTableWidget
- Implemented QSplitter for resizable panels
- Better error handling for JavaScript loading

## Fixed Issues

I've improved the lightweight chart with the following enhancements:

### 1. **Enhanced Error Detection**
- Added detailed console logging at each step
- Better validation of input data
- Clear error messages when something fails
- Checks for required columns in price data

### 2. **CDN Loading Handling**
- Added fallback error handling if CDN fails
- Clear message if internet is unavailable
- JavaScript error detection for missing library
- Visual feedback when chart library doesn't load

### 3. **Web Engine Configuration**
- Enabled proper settings for local content
- Configured error page display
- Better handling of remote resource loading

### 4. **Improved Logging**
- Console output shows each step of the process
- Displays data validation results
- Shows number of candles and trades processed
- Clear success/failure indicators (✓/✗/⚠)

## Common Issues & Solutions

### Issue 1: Chart Shows Empty/Blank
**Symptoms:** The Interactive Chart tab is blank or white

**Possible Causes:**
1. **No Internet Connection** - The chart loads from unpkg.com CDN
2. **Firewall/Proxy** - Corporate networks may block CDN access
3. **No Data** - Backtest didn't return price data

**Solution:**
- Check console output for error messages
- Verify internet connection
- Look at the status label at bottom of chart widget
- Check if other tabs (Trade Results, Equity Curve) have data

### Issue 2: "Failed to load chart - Check if internet is available"
**Symptoms:** Status message shows CDN error

**Solution:**
```
This means the lightweight-charts library couldn't load from the CDN.
Options:
1. Check your internet connection
2. Try again in a few moments
3. Check if unpkg.com is accessible
4. Use the old OHLC Chart tab instead (uses matplotlib, no internet needed)
```

### Issue 3: "Missing required columns"
**Symptoms:** Chart doesn't render, shows missing columns error

**Solution:**
This means the price data from MongoDB doesn't have the required format.
Required columns: date, open, high, low, close, volume

Check your MongoDB data structure in the backtest engine.

### Issue 4: Chart Shows but No Trade Markers
**Symptoms:** Candlesticks visible but no buy/sell arrows

**Possible Causes:**
1. No trades were executed
2. Trade markers are hidden (button says "Show Trades")
3. Trades are outside the visible time range

**Solution:**
- Click "Show Trades" button if it's hidden
- Check Trade Results tab to see if any trades executed
- Use mouse wheel to zoom out and see more timeframe

## Debug Output

When you run a backtest, check the console/terminal for output like this:

```
=== Lightweight Chart: plot_ohlc_with_trades called ===
Price data type: <class 'pandas.core.frame.DataFrame'>
Price data shape: (252, 6)
Trades count: 12
Price data columns: ['date', 'open', 'high', 'low', 'close', 'volume']
✓ Date column converted to datetime
✓ Ready to render chart
Rendering chart with 252 candles and 12 trades
✓ Prepared 252 chart data points
✓ Prepared 252 volume data points
Processing 12 trade markers...
✓ Prepared 12 trade markers (Buy: 6, Sell: 6)
✓ Created temporary HTML file: C:\Users\...\tmp1234.html
✓ Lightweight chart loaded successfully: 252 candles, 12 trades
```

## Testing the Chart

Run this test to verify the chart works:

1. Select any strategy (e.g., "moving_average")
2. Select a stock with good data (e.g., "AAPL")
3. Set date range (e.g., 1 year)
4. Click "Run Backtest"
5. Wait for completion
6. Click "Interactive Chart" tab
7. Check the status label at the bottom

**Expected Result:**
- Chart shows candlesticks with green/red colors
- Volume bars below the main chart
- Trade markers (if trades executed)
- Hover shows OHLC data
- Status: "Chart loaded: X candles, Y trades"

## Alternative: Use Old Chart

If the lightweight chart doesn't work, you can use the old matplotlib-based chart:

1. Look for the "OHLC Chart" tab (if available)
2. It works offline but is slower with large datasets
3. No interactivity but shows the same data

## Technical Details

**Requirements:**
- PyQt6-WebEngine (installed in requirements.txt)
- Internet connection for CDN
- JavaScript-enabled web engine

**CDN Used:**
```
https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js
```

**Browser Engine:**
- Uses Qt WebEngine (Chromium-based)
- Supports modern JavaScript
- Local file access configured

## Need More Help?

If you still have issues:

1. **Check Console Output** - Look for ✗ error messages
2. **Verify Data** - Check if other tabs show data
3. **Internet** - Ensure you can access unpkg.com
4. **Run Simple Test:**
   ```python
   from PyQt6.QtWebEngineWidgets import QWebEngineView
   print("WebEngine available")
   ```

The improvements I made should provide much better visibility into what's happening and where the issue might be!
