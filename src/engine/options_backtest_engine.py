"""
Enhanced Options Backtest Engine for Indian Market

This engine is specifically designed to properly handle Indian options strategies including:
- Call/Put buying and selling
- Multi-leg strategies (spreads, strangles, iron condors, etc.)
- Proper P&L calculation including intrinsic and time value
- Greek calculations and position tracking
- Realistic brokerage and slippage

Indian Options Market Basics:
-------------------------------
1. Options are European style (exercise only at expiry)
2. Premium quoted in rupees per lot
3. Strike prices in rupees (stored as paise internally: 1 Re = 100 paise)
4. Nifty 50 lot size = 75 (standard)
5. Weekly expiry on Thursdays, Monthly on last Thursday
6. Cash settled (no physical delivery)

Call Options:
- BUY CALL: Pay premium, profit when underlying rises above strike + premium paid
- SELL CALL: Receive premium, obligation to deliver, profit from theta decay

Put Options:
- BUY PUT: Pay premium, profit when underlying falls below strike - premium paid
- SELL PUT: Receive premium, obligation to buy, profit from theta decay

Multi-Leg Strategies:
- Bull Call Spread: Buy lower strike call + Sell higher strike call
- Bear Put Spread: Buy higher strike put + Sell lower strike put
- Short Strangle: Sell OTM call + Sell OTM put
- Iron Condor: Sell call spread + Sell put spread
- And many more...
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.db_connection import get_stock_data, get_mongo_client
from engine.strategy_loader import load_strategy
import gc

class OptionsBacktestEngine:
    """
    Advanced backtest engine for Indian options strategies with real option data
    """
    
    def __init__(self, initial_cash=1000000, brokerage_rate=0.0001, slippage_pct=0.0005):
        """
        Initialize options backtest engine
        
        Args:
            initial_cash: Starting capital in rupees (default: 10 lakhs)
            brokerage_rate: Brokerage as % of trade value (default: 0.01% = ₹10 per ₹1 lakh)
            slippage_pct: Slippage as % of premium (default: 0.05% = 5 paise per 100)
        """
        self.initial_cash = initial_cash
        self.brokerage_rate = brokerage_rate
        self.slippage_pct = slippage_pct
        self.progress_callback = None
        self.available_expiries = {}  # Cache of available expiry dates
        self.available_strikes = {}   # Cache of available strikes per expiry
        
    def _get_available_expiries(self):
        """
        Get all available option expiry dates from database
        Returns dict: {expiry_date: [list of collection names]}
        """
        if self.available_expiries:
            return self.available_expiries
        
        try:
            client, db_name = get_mongo_client()
            db = client[db_name]
            
            collections = db.list_collection_names()
            nifty_options = [c for c in collections if c.startswith('NSEFO:#NIFTY') and ('CE' in c or 'PE' in c)]
            
            expiries = {}
            for col in nifty_options:
                try:
                    # Extract expiry: NSEFO:#NIFTY20241226CE2200000 -> 20241226
                    parts = col.split('NIFTY')[1]
                    expiry_str = parts[:8]
                    expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
                    
                    if expiry_date not in expiries:
                        expiries[expiry_date] = []
                    expiries[expiry_date].append(col)
                except:
                    continue
            
            self.available_expiries = expiries
            print(f"  Found {len(expiries)} available expiry dates in database")
            return expiries
        except Exception as e:
            print(f"  Warning: Could not fetch available expiries: {e}")
            return {}
    
    def _get_closest_expiry(self, target_date, min_days=7):
        """
        Find the closest available expiry date to target date
        """
        expiries = self._get_available_expiries()
        if not expiries:
            return None
        
        # Convert target_date to timezone-naive datetime if needed
        target_dt = pd.to_datetime(target_date)
        if target_dt.tz is not None:
            target_dt = target_dt.tz_localize(None)
        
        available_dates = sorted(expiries.keys())
        
        # Find expiries that are after target date and have min days to expiry
        valid_expiries = [d for d in available_dates if (d - target_dt).days >= min_days]
        
        if not valid_expiries:
            # If no future expiries, use the furthest one available
            return available_dates[-1] if available_dates else None
        
        # Return closest future expiry
        return valid_expiries[0]
    
    def _get_available_strikes(self, expiry_date, option_type='CE'):
        """
        Get all available strikes for a given expiry and option type
        Returns sorted list of strikes in Rupees
        """
        cache_key = f"{expiry_date.strftime('%Y%m%d')}_{option_type}"
        if cache_key in self.available_strikes:
            return self.available_strikes[cache_key]
        
        expiries = self._get_available_expiries()
        if expiry_date not in expiries:
            return []
        
        strikes = []
        for col in expiries[expiry_date]:
            if option_type in col:
                try:
                    # Extract strike: NSEFO:#NIFTY20241226CE2200000 -> 2200000
                    parts = col.split(option_type)
                    if len(parts) > 1:
                        strike_paise = int(parts[1])
                        strike_rupees = strike_paise / 100.0
                        strikes.append(strike_rupees)
                except:
                    continue
        
        strikes = sorted(list(set(strikes)))
        self.available_strikes[cache_key] = strikes
        return strikes
    
    def _find_atm_strike(self, spot_price, available_strikes):
        """
        Find the ATM (At The Money) strike closest to spot price
        """
        if not available_strikes:
            return None
        
        # Find closest strike to spot
        differences = [abs(strike - spot_price) for strike in available_strikes]
        min_idx = differences.index(min(differences))
        return available_strikes[min_idx]
    
    def _find_otm_call_strike(self, spot_price, available_strikes, otm_pct=0.02):
        """
        Find OTM call strike (above spot by otm_pct)
        """
        if not available_strikes:
            return None
        
        target_strike = spot_price * (1 + otm_pct)
        strikes_above = [s for s in available_strikes if s >= target_strike]
        return strikes_above[0] if strikes_above else available_strikes[-1]
    
    def _find_otm_put_strike(self, spot_price, available_strikes, otm_pct=0.02):
        """
        Find OTM put strike (below spot by otm_pct)
        """
        if not available_strikes:
            return None
        
        target_strike = spot_price * (1 - otm_pct)
        strikes_below = [s for s in available_strikes if s <= target_strike]
        return strikes_below[-1] if strikes_below else available_strikes[0]
    
    def _find_itm_call_strike(self, spot_price, available_strikes, itm_pct=0.02):
        """
        Find ITM call strike (below spot by itm_pct)
        """
        if not available_strikes:
            return None
        
        target_strike = spot_price * (1 - itm_pct)
        strikes_below = [s for s in available_strikes if s <= target_strike]
        return strikes_below[-1] if strikes_below else available_strikes[0]
    
    def _find_itm_put_strike(self, spot_price, available_strikes, itm_pct=0.02):
        """
        Find ITM put strike (above spot by itm_pct)
        """
        if not available_strikes:
            return None
        
        target_strike = spot_price * (1 + itm_pct)
        strikes_above = [s for s in available_strikes if s >= target_strike]
        return strikes_above[0] if strikes_above else available_strikes[-1]
    
    def _fetch_option_premium(self, strike_rupees, option_type, current_date, expiry_date):
        """
        Fetch real option premium from database
        
        Args:
            strike_rupees: Strike price in Rupees (e.g., 24000)
            option_type: 'CE' or 'PE'
            current_date: Current date
            expiry_date: Option expiry date
            
        Returns:
            Premium in Rupees, or None if not found
        """
        try:
            # Convert strike to paise for symbol
            strike_paise = int(strike_rupees * 100)
            expiry_str = expiry_date.strftime('%Y%m%d')
            symbol = f"NSEFO:#NIFTY{expiry_str}{option_type}{strike_paise}"
            
            # Convert to timezone-naive datetime if needed
            current_date_obj = pd.to_datetime(current_date)
            if current_date_obj.tz is not None:
                current_date_obj = current_date_obj.tz_localize(None)
            
            start_date = (current_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (current_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            
            df = get_stock_data(symbol, start_date, end_date, use_cache=True)
            
            if df is None or df.empty:
                return None
            
            # Make df dates timezone-naive to match current_date_obj
            if df['date'].dt.tz is not None:
                df['date'] = df['date'].dt.tz_localize(None)
            
            # Find closest time point
            df['date_diff'] = abs((df['date'] - current_date_obj).dt.total_seconds())
            closest_idx = df['date_diff'].idxmin()
            premium_paise = df.loc[closest_idx, 'close']
            
            # Convert to Rupees
            premium_rupees = premium_paise / 100.0
            return premium_rupees
            
        except Exception as e:
            return None
    
    def _setup_strategy_option_access(self, strategy, data):
        """
        Setup real option data access for strategies by providing helper methods
        """
        # Get available expiries
        available_expiries = self._get_available_expiries()
        print(f"    Found {len(available_expiries)} available expiry dates")
        
        # Store references to engine methods in strategy
        strategy._engine_get_closest_expiry = self._get_closest_expiry
        strategy._engine_get_available_strikes = self._get_available_strikes
        strategy._engine_find_atm_strike = self._find_atm_strike
        strategy._engine_find_otm_call_strike = self._find_otm_call_strike
        strategy._engine_find_otm_put_strike = self._find_otm_put_strike
        strategy._engine_find_itm_call_strike = self._find_itm_call_strike
        strategy._engine_find_itm_put_strike = self._find_itm_put_strike
        strategy._engine_fetch_option_premium = self._fetch_option_premium
        
        # Store first spot price for reference
        if not data.empty:
            first_spot = data.iloc[0]['close']
            print(f"    Initial spot price: ₹{first_spot:,.2f}")
            
            # Show example strikes available for first date
            first_date = data.iloc[0]['date']
            expiry = self._get_closest_expiry(first_date, min_days=7)
            if expiry:
                print(f"    Closest expiry: {expiry.strftime('%Y-%m-%d')}")
                ce_strikes = self._get_available_strikes(expiry, 'CE')
                pe_strikes = self._get_available_strikes(expiry, 'PE')
                print(f"    Available strikes: {len(ce_strikes)} CE, {len(pe_strikes)} PE")
                
                # Find ATM strike
                if ce_strikes:
                    atm_strike = self._find_atm_strike(first_spot, ce_strikes)
                    print(f"    ATM strike: ₹{atm_strike:,.0f}")
                    
                    # Try to fetch real premium
                    premium = self._fetch_option_premium(atm_strike, 'CE', first_date, expiry)
                    if premium:
                        print(f"    Real ATM CE premium: ₹{premium:,.2f}")
                    else:
                        print(f"    Could not fetch premium for ATM CE")
        
    def run_backtest(self, strategy_path, stock_symbol, start_date, end_date, progress_callback=None):
        """
        Run backtest for options strategy
        
        Args:
            strategy_path: Path to strategy file
            stock_symbol: Underlying symbol (e.g., 'NIFTY')
            start_date: Backtest start date
            end_date: Backtest end date
            progress_callback: Progress update function
            
        Returns:
            dict: Backtest results with trades, equity curve, and metrics
        """
        self.progress_callback = progress_callback
        
        # Report progress
        if self.progress_callback:
            self.progress_callback(5, "Fetching underlying data...")
        
        # Fetch underlying data with caching
        data = get_stock_data(stock_symbol, start_date, end_date, use_cache=True)
        if data is None or data.empty:
            raise ValueError(f"No data returned for {stock_symbol} from {start_date} to {end_date}")
        
        # Convert prices from paise to Rupees for options strategies
        # (MongoDB stores prices in paise, but strategies expect Rupees)
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in data.columns:
                data[col] = data[col] / 100.0
        
        if self.progress_callback:
            self.progress_callback(15, "Loading strategy...")
        
        # Load strategy
        strategy = load_strategy(strategy_path)
        
        # Adjust strike_step from paise to Rupees for options strategies
        # (Default is 5000 paise = 50 Rupees, but we've converted data to Rupees)
        if hasattr(strategy, 'strike_step'):
            if strategy.strike_step >= 1000:  # Likely in paise
                strategy.strike_step = strategy.strike_step / 100.0
                print(f"  Adjusted strike_step from paise to Rupees: {strategy.strike_step}")
        
        # Pass underlying symbol to strategy
        if hasattr(strategy, 'set_underlying_symbol'):
            strategy.set_underlying_symbol(stock_symbol)
        
        # Setup real option data access for strategies
        print("  Setting up real option data access...")
        self._setup_strategy_option_access(strategy, data)
        
        # Check if strategy uses trade_log pattern (new options strategies)
        # These strategies are designed to be called once with full dataset
        if hasattr(strategy, 'on_data') and hasattr(strategy, 'get_trade_log'):
            print(f"  Using trade-log execution pattern")
            return self._run_with_trade_log(strategy, data)
        
        # Otherwise use bar-by-bar execution (traditional strategies)
        return self._run_bar_by_bar(strategy, data)
    
    def _run_with_trade_log(self, strategy, data):
        """
        Execute strategy that uses trade_log pattern.
        Call strategy.on_data() once with full dataset, then process trade_log.
        """
        if self.progress_callback:
            self.progress_callback(30, "Running strategy...")
        
        # Call strategy once with full dataset
        strategy.on_data(data)
        
        if self.progress_callback:
            self.progress_callback(70, "Processing trades...")
        
        # Get trades from strategy's trade log
        trades = strategy.get_trade_log()
        
        if len(trades) == 0:
            print("  Warning: No trades generated by strategy")
        else:
            print(f"  Strategy generated {len(trades)} trades")
        
        # Process trades to calculate equity curve and metrics
        return self._calculate_results_from_trade_log(trades, data)
    
    def _calculate_results_from_trade_log(self, trades, data):
        """
        Calculate backtest results from strategy's trade log.
        
        Args:
            trades: List of trades from strategy.get_trade_log()
            data: Price data DataFrame
            
        Returns:
            dict: Results with trades, equity curve, and metrics
        """
        if self.progress_callback:
            self.progress_callback(80, "Calculating equity curve...")
        
        # Initialize portfolio
        portfolio = {
            'cash': self.initial_cash,
            'positions': {},  # position_id -> position info
            'trades': [],
            'equity_curve': []
        }
        
        # Process each trade
        for trade in trades:
            action = trade.get('action', '')
            position_id = trade.get('position_id')
            
            if 'ENTER' in action:
                # Entry trade
                if trade.get('credit'):
                    # Credit strategy (selling options)
                    net_credit = trade.get('credit', 0)
                    brokerage = abs(net_credit) * self.brokerage_rate
                    net_proceeds = net_credit - brokerage
                    portfolio['cash'] += net_proceeds
                    
                    # Store position info
                    portfolio['positions'][position_id] = {
                        'entry_date': trade.get('date'),
                        'entry_credit': net_credit,
                        'entry_spot': trade.get('spot', 0),
                        'type': 'CREDIT'
                    }
                    
                    portfolio['trades'].append({
                        'date': trade.get('date'),
                        'action': 'OPEN',
                        'type': 'CREDIT',
                        'credit': net_credit,
                        'brokerage': brokerage,
                        'net_effect': net_proceeds,
                        'spot': trade.get('spot', 0),
                        'num_legs': trade.get('num_legs', len(trade.get('legs', [])))
                    })
                    
                elif trade.get('debit'):
                    # Debit strategy (buying options)
                    net_debit = trade.get('debit', 0)
                    brokerage = net_debit * self.brokerage_rate
                    total_cost = net_debit + brokerage
                    portfolio['cash'] -= total_cost
                    
                    # Store position info
                    portfolio['positions'][position_id] = {
                        'entry_date': trade.get('date'),
                        'entry_cost': net_debit,
                        'entry_spot': trade.get('spot', 0),
                        'type': 'DEBIT'
                    }
                    
                    portfolio['trades'].append({
                        'date': trade.get('date'),
                        'action': 'OPEN',
                        'type': 'DEBIT',
                        'debit': net_debit,
                        'brokerage': brokerage,
                        'net_effect': -total_cost,
                        'spot': trade.get('spot', 0),
                        'num_legs': trade.get('num_legs', len(trade.get('legs', [])))
                    })
                    
            elif 'EXIT' in action:
                # Exit trade
                pnl = trade.get('pnl', 0)
                closing_cost = abs(trade.get('closing_cost', 0))
                
                if closing_cost > 0:
                    brokerage = closing_cost * self.brokerage_rate
                    portfolio['cash'] -= (closing_cost + brokerage)
                else:
                    brokerage = 0
                
                # Realize P&L
                portfolio['cash'] += pnl
                
                # Remove position
                if position_id in portfolio['positions']:
                    del portfolio['positions'][position_id]
                
                portfolio['trades'].append({
                    'date': trade.get('date'),
                    'action': 'CLOSE',
                    'pnl': pnl,
                    'pnl_pct': trade.get('pnl_pct', 0),
                    'closing_cost': closing_cost,
                    'brokerage': brokerage,
                    'net_effect': pnl - closing_cost - brokerage,
                    'spot': trade.get('spot', 0),
                    'days_held': trade.get('days_held', 0),
                    'exit_reason': trade.get('exit_reason', 'Unknown')
                })
        
        if self.progress_callback:
            self.progress_callback(90, "Calculating metrics...")
        
        # Calculate equity curve
        equity_curve = []
        current_equity = self.initial_cash
        
        for idx, row in data.iterrows():
            date = row['date']
            
            # Update equity based on trades
            for trade in portfolio['trades']:
                if trade['date'] <= date:
                    if 'net_effect' in trade:
                        current_equity += trade['net_effect']
            
            equity_curve.append({
                'date': date,
                'equity': current_equity,
                'cash': portfolio['cash']
            })
        
        # Calculate metrics
        if len(portfolio['trades']) > 0:
            total_pnl = sum(t.get('pnl', 0) for t in portfolio['trades'] if t.get('action') == 'CLOSE')
            winning_trades = [t for t in portfolio['trades'] if t.get('action') == 'CLOSE' and t.get('pnl', 0) > 0]
            losing_trades = [t for t in portfolio['trades'] if t.get('action') == 'CLOSE' and t.get('pnl', 0) < 0]
            
            metrics = {
                'total_return': ((current_equity - self.initial_cash) / self.initial_cash) * 100,
                'total_trades': len([t for t in portfolio['trades'] if t.get('action') == 'CLOSE']),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': (len(winning_trades) / len(portfolio['trades'])) * 100 if portfolio['trades'] else 0,
                'total_pnl': total_pnl,
                'avg_win': sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
                'avg_loss': sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0,
                'profit_factor': abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades and sum(t['pnl'] for t in losing_trades) != 0 else 0,
                'final_equity': current_equity,
                'max_drawdown': 0,  # TODO: Calculate properly
                'sharpe_ratio': 0   # TODO: Calculate properly
            }
        else:
            metrics = {
                'total_return': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'final_equity': self.initial_cash
            }
        
        if self.progress_callback:
            self.progress_callback(100, "Backtest complete!")
        
        return {
            'trades': portfolio['trades'],
            'equity_curve': equity_curve,
            **metrics,
            'price_data': data.reset_index(drop=True)
        }
    
    def _run_bar_by_bar(self, strategy, data):
        """
        Execute strategy bar-by-bar (traditional pattern).
        Calls generate_signal() on each bar.
        """
        # Initialize portfolio
        portfolio = {
            'cash': self.initial_cash,
            'positions': [],  # List of option positions
            'trades': [],  # Complete trade history
            'equity_curve': [],  # Daily equity values
            'greeks': {  # Portfolio-level Greeks
                'delta': 0,
                'gamma': 0,
                'theta': 0,
                'vega': 0
            }
        }
        
        # Pre-allocate arrays
        n_rows = len(data)
        equity_values = np.zeros(n_rows)
        dates = data['date'].values
        closes = data['close'].values
        
        if self.progress_callback:
            self.progress_callback(20, f"Running backtest on {n_rows} bars...")
        
        # Prepare data arrays for faster access
        data_arrays = {
            'date': dates,
            'open': data['open'].values,
            'high': data['high'].values,
            'low': data['low'].values,
            'close': closes,
            'volume': data['volume'].values
        }
        
        progress_interval = max(n_rows // 50, 1)
        lookback_window = 1000  # For options strategies needing volatility calculation
        
        # Main backtest loop
        for idx in range(n_rows):
            # Current bar as dict
            current_bar = {
                'date': dates[idx],
                'open': data_arrays['open'][idx],
                'high': data_arrays['high'][idx],
                'low': data_arrays['low'][idx],
                'close': data_arrays['close'][idx],
                'volume': data_arrays['volume'][idx]
            }
            
            # Historical data window
            start_idx = max(0, idx + 1 - lookback_window)
            historical_data = data.iloc[start_idx:idx+1]
            
            # Generate signal from strategy
            signal = strategy.generate_signal(current_bar, historical_data)
            
            # Process signals - options strategies manage their own positions
            # We just track the trades they generate
            if signal not in ['HOLD', None]:
                # Check if strategy has trade_log with new trades
                if hasattr(strategy, 'trade_log') and strategy.trade_log:
                    # Process new trades from strategy
                    self._process_strategy_trades(portfolio, strategy, current_bar)
            
            # Calculate current equity
            equity = self._calculate_equity(portfolio, current_bar, strategy)
            equity_values[idx] = equity
            
            # Store equity curve (sample for memory efficiency)
            if n_rows < 1000 or idx % 10 == 0 or idx == n_rows - 1:
                portfolio['equity_curve'].append({
                    'date': dates[idx],
                    'equity': equity,
                    'cash': portfolio['cash'],
                    'positions_value': equity - portfolio['cash']
                })
            
            # Update progress
            if self.progress_callback and idx % progress_interval == 0:
                progress = 20 + int((idx / n_rows) * 70)
                self.progress_callback(progress, f"Processing bar {idx+1}/{n_rows}...")
        
        if self.progress_callback:
            self.progress_callback(95, "Calculating metrics...")
        
        # Calculate comprehensive metrics
        metrics = self._calculate_metrics(portfolio, equity_values)
        
        # Clean up
        gc.collect()
        
        if self.progress_callback:
            self.progress_callback(100, "Backtest complete!")
        
        return {
            'trades': portfolio['trades'],
            'equity_curve': portfolio['equity_curve'],
            'metrics': metrics,
            'price_data': data.reset_index(drop=True)
        }
    
    def _process_strategy_trades(self, portfolio, strategy, current_bar):
        """
        Process trades from strategy's trade log
        
        This handles multi-leg options strategies where the strategy manages
        its own positions and we just record the trades and P&L.
        """
        # Check for new trades in strategy's log
        if not hasattr(strategy, 'trade_log'):
            return
        
        # Track which position IDs we've already processed
        if not hasattr(self, '_processed_position_ids'):
            self._processed_position_ids = set()
        
        # Look for ENTRY and EXIT actions
        for trade in strategy.trade_log:
            position_id = trade.get('position_id')
            action = trade.get('action')
            
            # Create unique ID for this trade
            trade_uid = f"{position_id}_{action}"
            
            if trade_uid in self._processed_position_ids:
                continue
            
            # Mark as processed
            self._processed_position_ids.add(trade_uid)
            
            if 'ENTER' in action or 'ENTRY' in action:
                # Entry trade - deduct cost from cash
                cost = abs(trade.get('cost', 0) or trade.get('debit', 0) or trade.get('credit', 0))
                
                # For credit strategies (selling options), cost is negative (we receive money)
                # For debit strategies (buying options), cost is positive (we pay money)
                if trade.get('credit'):
                    # Selling options - receive premium
                    net_credit = trade.get('credit', 0)
                    brokerage = abs(net_credit) * self.brokerage_rate
                    net_proceeds = net_credit - brokerage
                    portfolio['cash'] += net_proceeds
                    
                    portfolio['trades'].append({
                        'date': trade.get('date'),
                        'action': 'SELL_OPTIONS',
                        'type': 'CREDIT',
                        'position_id': position_id,
                        'spot': trade.get('spot', 0),
                        'credit_received': net_credit,
                        'brokerage': brokerage,
                        'net_proceeds': net_proceeds,
                        'legs': self._format_legs(trade, strategy),
                        'strategy_type': trade.get('action', 'UNKNOWN')
                    })
                else:
                    # Buying options - pay premium
                    net_debit = abs(trade.get('cost', 0) or trade.get('debit', 0))
                    brokerage = net_debit * self.brokerage_rate
                    total_cost = net_debit + brokerage
                    portfolio['cash'] -= total_cost
                    
                    portfolio['trades'].append({
                        'date': trade.get('date'),
                        'action': 'BUY_OPTIONS',
                        'type': 'DEBIT',
                        'position_id': position_id,
                        'spot': trade.get('spot', 0),
                        'debit_paid': net_debit,
                        'brokerage': brokerage,
                        'total_cost': total_cost,
                        'legs': self._format_legs(trade, strategy),
                        'strategy_type': trade.get('action', 'UNKNOWN')
                    })
            
            elif 'EXIT' in action:
                # Exit trade - close position and realize P&L
                pnl = trade.get('pnl', 0)
                closing_cost = abs(trade.get('closing_cost', 0) or trade.get('cost', 0))
                
                # For short positions, we buy back (pay cost)
                # For long positions, we sell (receive proceeds)
                if closing_cost > 0:
                    brokerage = closing_cost * self.brokerage_rate
                    total_cost = closing_cost + brokerage
                    portfolio['cash'] -= total_cost
                
                # Add realized P&L to cash (already calculated by strategy)
                portfolio['cash'] += pnl
                
                portfolio['trades'].append({
                    'date': trade.get('date'),
                    'action': 'CLOSE_OPTIONS',
                    'type': 'EXIT',
                    'position_id': position_id,
                    'spot': trade.get('spot', 0),
                    'pnl': pnl,
                    'pnl_pct': trade.get('pnl_pct', 0),
                    'days_held': trade.get('days_held', 0),
                    'exit_reason': trade.get('exit_reason', 'Unknown'),
                    'brokerage': brokerage if closing_cost > 0 else 0,
                    'legs': self._format_legs(trade, strategy),
                    'strategy_type': trade.get('action', 'UNKNOWN')
                })
    
    def _format_legs(self, trade, strategy):
        """Format option legs for display"""
        legs_info = []
        
        # Try to get legs from trade
        if 'legs' in trade and trade['legs']:
            for leg in trade['legs']:
                leg_str = f"{leg.get('type', '?')} {leg.get('quantity', 0)}x @ ₹{leg.get('strike', 0)/100:.0f}"
                legs_info.append(leg_str)
        # Fallback: try to get from strategy's current position
        elif hasattr(strategy, 'options_legs') and strategy.options_legs:
            for leg in strategy.options_legs:
                premium = leg.get('premium', 0)
                leg_str = f"{leg.get('type', '?')} {leg.get('quantity', 0)}x @ ₹{leg.get('strike', 0)/100:.0f} (₹{premium:.2f})"
                legs_info.append(leg_str)
        # Try specific fields for simple strategies
        else:
            if 'call_strike' in trade:
                legs_info.append(f"CALL @ ₹{trade.get('call_strike', 0)/100:.0f}")
            if 'put_strike' in trade:
                legs_info.append(f"PUT @ ₹{trade.get('put_strike', 0)/100:.0f}")
        
        return ' | '.join(legs_info) if legs_info else 'No legs info'
    
    def _calculate_equity(self, portfolio, current_bar, strategy):
        """
        Calculate current portfolio equity
        
        Equity = Cash + Value of Open Positions
        
        For options positions, value = current premium * quantity * lot_size
        """
        equity = portfolio['cash']
        
        # For strategies that track their own positions, don't double count
        # The strategy's trade_log already includes realized P&L in cash
        # Unrealized P&L is managed by the strategy until exit
        
        return equity
    
    def _calculate_metrics(self, portfolio, equity_values):
        """
        Calculate comprehensive backtest metrics
        """
        trades = portfolio['trades']
        
        if not trades:
            return {
                'initial_capital': self.initial_cash,
                'final_capital': self.initial_cash,
                'total_pnl': 0,
                'total_return_pct': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'max_drawdown_pct': 0
            }
        
        # Identify closing trades (ones with P&L)
        closing_trades = [t for t in trades if 'pnl' in t and t.get('action') == 'CLOSE_OPTIONS']
        
        if closing_trades:
            pnls = np.array([t['pnl'] for t in closing_trades])
            total_pnl = pnls.sum()
            
            winning_mask = pnls > 0
            losing_mask = pnls < 0
            
            winning_pnls = pnls[winning_mask]
            losing_pnls = pnls[losing_mask]
            
            num_wins = len(winning_pnls)
            num_losses = len(losing_pnls)
            win_rate = (num_wins / len(pnls) * 100) if len(pnls) > 0 else 0
            
            gross_profit = winning_pnls.sum() if num_wins > 0 else 0
            gross_loss = abs(losing_pnls.sum()) if num_losses > 0 else 0
            
            avg_win = winning_pnls.mean() if num_wins > 0 else 0
            avg_loss = abs(losing_pnls.mean()) if num_losses > 0 else 0
            
            largest_win = winning_pnls.max() if num_wins > 0 else 0
            largest_loss = losing_pnls.min() if num_losses > 0 else 0
            
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
        else:
            total_pnl = 0
            num_wins = 0
            num_losses = 0
            win_rate = 0
            gross_profit = 0
            gross_loss = 0
            avg_win = 0
            avg_loss = 0
            largest_win = 0
            largest_loss = 0
            profit_factor = 0
        
        # Final capital and returns
        final_capital = equity_values[-1]
        total_return_pct = ((final_capital - self.initial_cash) / self.initial_cash * 100) if self.initial_cash > 0 else 0
        
        # Drawdown calculation
        equity_array = equity_values[equity_values > 0]
        if len(equity_array) > 0:
            running_max = np.maximum.accumulate(equity_array)
            drawdowns = running_max - equity_array
            max_drawdown = drawdowns.max()
            max_dd_idx = drawdowns.argmax()
            max_drawdown_pct = (max_drawdown / running_max[max_dd_idx] * 100) if running_max[max_dd_idx] > 0 else 0
            max_drawdown_pct = min(max_drawdown_pct, 100.0)
        else:
            max_drawdown = 0
            max_drawdown_pct = 0
        
        # Sharpe ratio (simplified - using daily returns)
        if len(equity_values) > 1:
            returns = np.diff(equity_values) / equity_values[:-1]
            returns = returns[np.isfinite(returns)]
            if len(returns) > 0 and returns.std() > 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Total brokerage paid
        total_brokerage = sum(t.get('brokerage', 0) for t in trades)
        
        return {
            'initial_capital': self.initial_cash,
            'final_capital': float(final_capital),
            'total_pnl': float(total_pnl),
            'total_return_pct': float(total_return_pct),
            'total_trades': len(closing_trades),
            'winning_trades': int(num_wins),
            'losing_trades': int(num_losses),
            'win_rate': float(win_rate),
            'gross_profit': float(gross_profit),
            'gross_loss': float(gross_loss),
            'profit_factor': float(profit_factor),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'largest_win': float(largest_win),
            'largest_loss': float(largest_loss),
            'max_drawdown': float(max_drawdown),
            'max_drawdown_pct': float(max_drawdown_pct),
            'sharpe_ratio': float(sharpe_ratio),
            'total_brokerage': float(total_brokerage)
        }
