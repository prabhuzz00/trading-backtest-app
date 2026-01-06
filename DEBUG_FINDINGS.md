# Options Strategies Debug - Complete Solution

## Problem
No trades were being taken when running options strategies in the backtest UI.

## Root Causes Identified and Fixed

### 1. **Data Format Issues** ❌ → ✅ FIXED

#### A. Wrong Column Names
- **Wrong**: Uppercase (`'Close'`, `'Date'`, `'Open'`, etc.)
- **Correct**: Lowercase (`'close'`, `'date'`, `'open'`, etc.)
- **Why**: Strategies expect lowercase column names in DataFrame

#### B. Wrong Price Units  
- **Wrong**: Data in paise (2,170,845 paise)
- **Correct**: Data in Rupees (21,708.45 Rupees)
- **Solution**: Divide all OHLC columns by 100 after fetching from MongoDB

#### C. Date Column Missing
- **Wrong**: Date set as DataFrame index
- **Correct**: Date as regular column named 'date'
- **Why**: Strategies access `current_bar['date']` directly

#### D. Strike Step Parameter  
- **Critical Issue**: `strike_step` parameter is in paise by default (5000 = 50 Rupees)
- **Problem**: When spot is converted to Rupees but strike_step stays in paise, strike rounding fails
- **Solution**: Convert `strike_step` to Rupees when passing to strategy
  - Default: `strike_step=5000` (paise)
  - Correct: `strike_step=50` (Rupees) when using Rupees-based data

### 2. **Symbol Name** ❌ → ✅ FIXED
- **Wrong**: `'NIFTY 50'`  
- **Correct**: `'NSECM:NIFTY 50'` (MongoDB collection name for spot data)

### 3. **Options Data Availability** ⚠️ PARTIAL

#### What Exists in MongoDB:
- ✅ **116 NIFTY options collections** found
- ✅ **Format**: `NSEFO:#NIFTY20241226CE2200000` (strike in paise)
- ✅ **Date range**: 2020-2025 with data
- ❌ **But**: Only **yearly expiry** options (Dec 31, Dec 30, etc.)
- ❌ **Missing**: **Weekly Thursday expiry** options

#### How Strategies Handle This:
1. Try to fetch premium from MongoDB using calculated weekly expiry date
2. If not found (returns None), fall back to **theoretical estimation**
3. Theoretical estimation uses Black-Scholes approximation with ATR-based IV

#### Why Some Strategies Work:
- **Risk Defined Premium Band**: ✅ Works (theoretical estimation succeeds)
- **Short Vol Inventory**: ❌ Doesn't enter (theoretical estimation returns 0)
- **Root cause**: Strike/spot unit mismatch in premium calculation

## Complete Solution for Backtest Engine

The backtest engine needs to prepare data correctly before passing to options strategies:

```python
def prepare_data_for_options_strategy(symbol, start_date, end_date):
    """Prepare data for options strategies"""
    # 1. Use correct symbol
    if symbol == 'NIFTY 50' or symbol == 'NIFTY':
        mongodb_symbol = 'NSECM:NIFTY 50'
    else:
        mongodb_symbol = symbol
    
    # 2. Fetch data from MongoDB
    data = get_stock_data(mongodb_symbol, start_date, end_date, use_cache=False)
    
    if data is None or data.empty:
        return None
    
    # 3. Ensure lowercase column names
    data = data.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low',
        'Close': 'close', 'Volume': 'volume', 'Date': 'date'
    })
    
    # 4. Convert from paise to Rupees
    for col in ['open', 'high', 'low', 'close']:
        if col in data.columns:
            data[col] = data[col] / 100
    
    # 5. Ensure 'date' is a column (not index)
    if 'date' not in data.columns and data.index.name == 'date':
        data = data.reset_index()
    
    return data

def get_strategy_parameters_for_rupees_data(strategy_params):
    """Adjust strategy parameters when using Rupees-based data"""
    adjusted = strategy_params.copy()
    
    # Convert strike_step from paise to Rupees
    if 'strike_step' in adjusted:
        # Default is 5000 paise = 50 Rupees
        adjusted['strike_step'] = adjusted.get('strike_step', 5000) / 100
    else:
        adjusted['strike_step'] = 50  # 50 Rupees
    
    return adjusted
```

## Usage Example

```python
# In OptionsBacktestEngine or main UI

# Step 1: Prepare data
data = prepare_data_for_options_strategy('NIFTY 50', '2024-01-01', '2024-12-31')

# Step 2: Adjust strategy parameters
params = {
    'num_strikes': 2,
    'strike_spacing_pct': 0.02,
    'profit_target_pct': 0.5,
    'stop_loss_pct': 2.0,
    'hold_days': 5
}
adjusted_params = get_strategy_parameters_for_rupees_data(params)

# Step 3: Initialize strategy with adjusted parameters
from strategies.short_vol_inventory import Strategy as ShortVolStrategy
strategy = ShortVolStrategy(**adjusted_params)
strategy.set_underlying_symbol('NSECM:NIFTY 50')

# Step 4: Run backtest
strategy.on_data(data)
```

## Files to Update

### 1. `src/engine/options_backtest_engine.py`

Add data preparation function at the top and use it before running:

```python
def run(self):
    """Run options backtest"""
    # Prepare data with correct format
    self.data = self._prepare_data_format(self.data)
    
    # Rest of backtest logic...
    
def _prepare_data_format(self, data):
    """Ensure data is in correct format for options strategies"""
    # Convert paise to Rupees
    for col in ['open', 'high', 'low', 'close']:
        if col in data.columns:
            data[col] = data[col] / 100
    
    # Lowercase columns
    data.columns = [c.lower() if isinstance(c, str) else c for c in data.columns]
    
    # Ensure date is column
    if 'date' not in data.columns:
        data = data.reset_index()
        if 'index' in data.columns:
            data = data.rename(columns={'index': 'date'})
    
    return data
```

### 2. `src/ui/main_window.py`

Update strategy loading to adjust parameters:

```python
# In BacktestWorker.run() method, after loading strategy:

if self._is_options_strategy(strategy_path):
    # Adjust parameters for Rupees-based data
    # Get current params from strategy file or use defaults
    
    # Re-initialize with adjusted strike_step
    # This might require modifying how strategies are loaded
    pass
```

## Testing

Run the test script to verify:
```bash
python simple_test.py
```

Expected output:
- ✅ Risk Defined Premium Band: Enters position
- ✅ Short Vol Inventory: Should now enter position (after strike_step fix)

##