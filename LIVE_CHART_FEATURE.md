# Live Chart Feature

## Overview
Added a new "Live Chart" tab that allows you to fetch and visualize OHLCV data directly from MongoDB for any selected instrument, independent of backtesting.

## New Features

### 📉 Live Chart Tab
- **First tab** in the application for quick access to market data
- Fetches OHLCV (Open, High, Low, Close, Volume) data from MongoDB
- Displays data using lightweight-charts library (same as backtest charts)
- Includes volume panel below the main price chart

### Key Capabilities

1. **Dynamic Data Loading**
   - Select any stock from the sidebar
   - Click "Load Chart" to fetch data
   - Background worker prevents UI freezing during data fetch

2. **Date Range Selection**
   - Customizable start and end dates
   - Default: Last 3 months of data
   - Easy date picker interface

3. **Multiple Chart Types**
   - **Candlestick** - Traditional OHLC candles (default)
   - **Line** - Close price line chart
   - **Area** - Filled area chart

4. **Volume Visualization**
   - Color-coded volume bars (green for up, red for down)
   - Synchronized with main chart scrolling/zooming
   - 30% of chart height dedicated to volume

## How to Use

### Basic Workflow
1. **Select a Stock**
   - Click on any stock in the left sidebar
   - The stock symbol appears in the Live Chart controls

2. **Adjust Date Range** (optional)
   - Modify "From" and "To" dates as needed
   - Default shows last 3 months

3. **Load Chart**
   - Click the "📊 Load Chart" button
   - Progress bar shows loading status
   - Chart renders when data is ready

4. **Interact with Chart**
   - Scroll to zoom in/out
   - Drag to pan left/right
   - Hover to see OHLCV values
   - Change chart type using dropdown

### Chart Types

**Candlestick**
- Best for detailed price action analysis
- Shows open, high, low, close
- Green = bullish, Red = bearish

**Line**
- Simple close price visualization
- Clean and minimal
- Good for trend overview

**Area**
- Filled area under close price
- Visual emphasis on price movement
- Professional appearance

## Technical Details

### Data Source
- Fetches from MongoDB collections
- Uses existing `get_stock_data()` function
- Efficient caching system
- Background threading for non-blocking loads

### Chart Library
- lightweight-charts v4.1.0
- WebEngine-based rendering
- Dark theme matching platform style
- Synchronized price/volume panels

### Performance
- Background data fetching
- Progress indicators
- Cached data retrieval
- No UI blocking during loads

## Tab Organization

The tabs are now organized as:
1. **📉 Live Chart** - View any stock's data (NEW)
2. **📊 Backtest Chart** - Results of backtest runs
3. **📈 Equity Curve** - Portfolio performance over time
4. **📋 Summary** - Backtest metrics and statistics
5. **💼 Trades** - Detailed trade history

## Status Bar Information

When chart loads successfully, status bar shows:
- Number of candles loaded
- Date range (first to last candle)
- Latest closing price
- Example: `✓ Loaded 250 candles | Period: 2025-09-23 to 2025-12-23 | Latest: ₹1,769.00`

## Error Handling

The widget handles:
- No data available for date range
- MongoDB connection errors
- Invalid symbols
- Library loading failures

All errors display user-friendly messages.

## Integration

### Connected Components
- **Stock Sidebar** - Symbol selection triggers chart update
- **Top Toolbar** - Maintains symbol context
- **Status Bar** - Shows loading progress and results

### Independent Operation
- Does NOT require running a backtest
- Fetches data on-demand
- Separate from backtest results
- Can be used for quick market analysis

## Future Enhancements

Potential improvements:
- Add technical indicators (MA, RSI, MACD, etc.)
- Multiple timeframes (1min, 5min, daily, weekly)
- Drawing tools (trendlines, fibonacci, etc.)
- Export chart as image
- Real-time data updates (if supported)
- Comparison with other symbols
- Custom date presets (1D, 1W, 1M, 3M, 1Y, All)
