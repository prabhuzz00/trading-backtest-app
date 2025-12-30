import pandas as pd
import numpy as np
from utils.db_connection import get_stock_data
from engine.strategy_loader import load_strategy
from numba import jit
import gc

class BacktestEngine:
    def __init__(self, initial_cash=100000, brokerage_rate=0.00007):
        self.initial_cash = initial_cash
        # Brokerage: ₹7000 per ₹1 crore = 0.007% = 0.00007
        self.brokerage_rate = brokerage_rate
        self.progress_callback = None

    def run_backtest(self, strategy_path, stock_symbol, start_date, end_date, progress_callback=None):
        self.progress_callback = progress_callback
        
        # Report progress
        if self.progress_callback:
            self.progress_callback(5, "Fetching data from database...")
        
        # Fetch data with caching enabled
        data = get_stock_data(stock_symbol, start_date, end_date, use_cache=True)
        if data is None or data.empty:
            raise ValueError("No data returned for symbol/date range")

        if self.progress_callback:
            self.progress_callback(15, "Loading strategy...")
        
        strategy = load_strategy(strategy_path)
        
        # Pass the underlying symbol to strategy if it supports it (for options strategies)
        if hasattr(strategy, 'set_underlying_symbol'):
            strategy.set_underlying_symbol(stock_symbol)

        portfolio = {
            'cash': self.initial_cash,
            'positions': {},  # symbol: shares (positive = long, negative = short)
            'trades': [],
            'equity_curve': [],
            'entry_prices': {},  # Track entry prices for P&L calculation
            'position_types': {}  # Track whether position is LONG or SHORT
        }

        # Pre-allocate arrays for better memory efficiency
        n_rows = len(data)
        equity_values = np.zeros(n_rows)
        dates = data['date'].values
        closes = data['close'].values
        
        if self.progress_callback:
            self.progress_callback(20, f"Running backtest on {n_rows} data points...")
        
        # Convert data to numpy arrays for faster access
        data_arrays = {
            'date': dates,
            'open': data['open'].values,
            'high': data['high'].values,
            'low': data['low'].values,
            'close': closes,
            'volume': data['volume'].values
        }
        
        progress_interval = max(n_rows // 50, 1)  # Update progress 50 times
        
        # **PERFORMANCE OPTIMIZATION**: Use a rolling window instead of full history
        # Most strategies only need recent data (e.g., 200 bars for MA, 14 for RSI)
        # INCREASED for options strategies that need more history for volatility calc
        lookback_window = 1000  # Increased from 500 for options strategies
        
        # Use itertuples for faster iteration (5-10x faster than iterrows)
        for idx in range(n_rows):
            # Create row dict without unnecessary conversions
            row_dict = {
                'date': dates[idx],
                'open': data_arrays['open'][idx],
                'high': data_arrays['high'][idx],
                'low': data_arrays['low'][idx],
                'close': data_arrays['close'][idx],
                'volume': data_arrays['volume'][idx]
            }
            
            # **PERFORMANCE FIX**: Only pass recent data window, not entire history
            # This dramatically speeds up backtests on large datasets
            start_idx = max(0, idx + 1 - lookback_window)
            current_hist_data = data.iloc[start_idx:idx+1]
            
            signal = strategy.generate_signal(row_dict, current_hist_data)
            if signal in ['BUY', 'BUY_LONG']:
                self.execute_buy_long(portfolio, row_dict, stock_symbol, strategy)
            elif signal in ['SELL', 'SELL_LONG']:
                self.execute_sell_long(portfolio, row_dict, stock_symbol, strategy)
            elif signal == 'SELL_SHORT':
                self.execute_sell_short(portfolio, row_dict, stock_symbol, strategy)
            elif signal == 'BUY_SHORT':
                self.execute_buy_short(portfolio, row_dict, stock_symbol, strategy)

            # Calculate equity for this bar
            equity = self.calculate_equity_fast(portfolio, closes[idx])
            equity_values[idx] = equity
            
            # **OPTIMIZATION**: Store equity curve less frequently to save memory/time
            # Only store every 10th point or all points if dataset is small
            if n_rows < 1000 or idx % 10 == 0 or idx == n_rows - 1:
                portfolio['equity_curve'].append({
                    'date': dates[idx],
                    'equity': equity
                })
            
            # Update progress periodically
            if self.progress_callback and idx % progress_interval == 0:
                progress = 20 + int((idx / n_rows) * 70)
                self.progress_callback(progress, f"Processing bar {idx+1}/{n_rows}...")

        if self.progress_callback:
            self.progress_callback(95, "Calculating metrics...")
        
        # Calculate comprehensive metrics using ALL equity values for accurate max drawdown
        # equity_values contains every bar, equity_curve is sampled for memory efficiency
        metrics = self.calculate_metrics_fast(portfolio, self.initial_cash, equity_values)
        
        # Clean up to free memory
        gc.collect()
        
        if self.progress_callback:
            self.progress_callback(100, "Backtest complete!")
        
        return {
            'trades': portfolio['trades'],
            'equity_curve': portfolio['equity_curve'],
            'metrics': metrics,
            'price_data': data.reset_index(drop=True) if hasattr(data, 'reset_index') else data
        }

    def execute_buy_long(self, portfolio, row, symbol, strategy=None):
        """Open or add to a long position."""
        price = float(row.get('close', 0))
        if price <= 0:
            return
        
        # For options strategies with small premiums, ensure at least 1 position
        # Check if this is an options strategy (has options_legs)
        is_options = strategy and hasattr(strategy, 'options_legs') and strategy.options_legs
        
        if is_options:
            # For options: use fixed position size of 1 lot, cost is the net debit
            shares = 1  # 1 position/lot
            # Use entry_price from strategy if available (net debit paid for spread)
            if hasattr(strategy, 'entry_price') and strategy.entry_price is not None:
                cost = abs(strategy.entry_price)  # Net debit for the spread
            else:
                cost = price * 0.01  # Fallback: 1% of underlying price as spread cost
        else:
            # For equity: calculate shares based on available cash and price
            shares = int(portfolio['cash'] * 0.95 / price)
            cost = shares * price
        
        # Calculate brokerage charges
        brokerage = cost * self.brokerage_rate
        total_cost = cost + brokerage
        
        # Get options info from strategy if available
        options_info = ""
        if strategy and hasattr(strategy, 'options_legs') and strategy.options_legs:
            legs_info = []
            for leg in strategy.options_legs:
                premium = leg.get('entry_premium', 0) / 100.0  # Divide by 100 for display
                leg_str = f"{leg['strike']} {leg['type']} {leg['side']} @₹{premium:.2f}"
                legs_info.append(leg_str)
            options_info = " | ".join(legs_info)
        
        if shares > 0 and total_cost <= portfolio['cash']:
            portfolio['cash'] -= total_cost
            portfolio['positions'][symbol] = portfolio['positions'].get(symbol, 0) + shares
            # For options, store the actual cost paid; for equity, store the price
            if is_options:
                portfolio['entry_prices'][symbol] = cost  # Store cost, not price
            else:
                portfolio['entry_prices'][symbol] = price  # Store price for equity
            portfolio['position_types'][symbol] = 'LONG'
            portfolio['trades'].append({
                'date': row.get('date'),
                'action': 'BUY_LONG',
                'trade_type': 'LONG',
                'symbol': symbol,
                'shares': shares,
                'price': price,
                'value': cost,
                'brokerage': brokerage,
                'total_cost': total_cost,
                'pnl': 0,
                'pnl_pct': 0,
                'quantity': shares,
                'options_info': options_info
            })

    def execute_sell_long(self, portfolio, row, symbol, strategy=None):
        """Close a long position."""
        shares = portfolio['positions'].get(symbol, 0)
        if shares <= 0:
            return
        price = float(row.get('close', 0))
        
        # For options strategies, check if this is an options symbol
        is_options_symbol = 'NSEFO' in symbol
        
        if is_options_symbol and strategy:
            # Get entry cost (what we paid for the spread)
            entry_cost = portfolio['entry_prices'].get(symbol, 0)
            
            # Get P&L from strategy's trade log (most recent trade)
            if hasattr(strategy, 'trade_log') and strategy.trade_log:
                last_trade = strategy.trade_log[-1]
                
                # The strategy calculates P&L before clearing legs
                # So we can use it directly
                pnl_from_strategy = last_trade.get('pnl', 0)
                
                # Calculate proceeds: entry_cost + pnl = exit_value
                # Entry cost is positive (what we paid), pnl can be positive or negative
                proceeds = abs(entry_cost) + pnl_from_strategy
                
                # Sanity check: proceeds should be between 0 and max_value
                if hasattr(strategy, 'strike_spacing'):
                    # Get lot size (default to 1 if not specified)
                    lot_size = getattr(strategy, 'lot_size', 1)
                    max_value = strategy.strike_spacing * lot_size  # Max value with lot size
                    proceeds = max(0, min(proceeds, max_value))
                else:
                    # Ensure non-negative
                    proceeds = max(0, proceeds)
            else:
                # Fallback if no trade log
                proceeds = entry_cost * 0.5  # Assume 50% loss as conservative fallback
        else:
            # Standard equity calculation
            proceeds = shares * price
        
        # Calculate brokerage charges
        brokerage = proceeds * self.brokerage_rate
        net_proceeds = proceeds - brokerage
        
        portfolio['cash'] += net_proceeds
        
        # Calculate P&L (including brokerage from both buy and sell)
        entry_price = portfolio['entry_prices'].get(symbol, price)
        
        if is_options_symbol:
            # For options, use the actual cost paid (entry_price stores the cost)
            entry_value = entry_price
        else:
            # For equity
            entry_value = entry_price * shares
            
        entry_brokerage = entry_value * self.brokerage_rate
        total_brokerage = entry_brokerage + brokerage
        
        # Net P&L after all costs
        pnl = proceeds - entry_value - total_brokerage
        pnl_pct = (pnl / (entry_value + entry_brokerage) * 100) if entry_value > 0 else 0
        
        # Get options info from strategy if available
        options_info = ""
        if strategy and hasattr(strategy, 'options_legs') and hasattr(strategy, 'trade_log') and strategy.trade_log:
            last_trade = strategy.trade_log[-1]
            legs_info = []
            for leg in last_trade.get('legs', []):
                premium = leg.get('entry_premium', 0) / 100.0  # Divide by 100 for display
                leg_str = f"{leg['strike']} {leg['type']} {leg['side']} @₹{premium:.2f}"
                legs_info.append(leg_str)
            if legs_info:
                options_info = " | ".join(legs_info)
                exit_reason = last_trade.get('exit_reason', '')
                if exit_reason:
                    options_info += f" ({exit_reason})"
        
        portfolio['positions'][symbol] = 0
        portfolio['position_types'].pop(symbol, None)
        portfolio['trades'].append({
            'date': row.get('date'),
            'action': 'SELL_LONG',
            'trade_type': 'LONG',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'value': proceeds,
            'brokerage': brokerage,
            'total_brokerage': total_brokerage,
            'net_proceeds': net_proceeds,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'quantity': shares,
            'options_info': options_info
        })
    
    def execute_sell_short(self, portfolio, row, symbol, strategy=None):
        """Open a short position (sell first, buy later)."""
        price = float(row.get('close', 0))
        if price <= 0:
            return
        
        # Calculate shares based on available cash (same as long)
        shares = int(portfolio['cash'] * 0.95 / price)
        proceeds = shares * price
        
        # Calculate brokerage charges
        brokerage = proceeds * self.brokerage_rate
        net_proceeds = proceeds - brokerage
        
        # Get options info from strategy if available
        options_info = ""
        if strategy and hasattr(strategy, 'options_legs') and strategy.options_legs:
            legs_info = []
            for leg in strategy.options_legs:
                premium = leg.get('entry_premium', 0) / 100.0  # Divide by 100 for display
                leg_str = f"{leg['strike']} {leg['type']} {leg['side']} @₹{premium:.2f}"
                legs_info.append(leg_str)
            options_info = " | ".join(legs_info)
        
        if shares > 0:
            portfolio['cash'] += net_proceeds  # Add proceeds from short sale
            portfolio['positions'][symbol] = portfolio['positions'].get(symbol, 0) - shares  # Negative for short
            portfolio['entry_prices'][symbol] = price
            portfolio['position_types'][symbol] = 'SHORT'
            portfolio['trades'].append({
                'date': row.get('date'),
                'action': 'SELL_SHORT',
                'trade_type': 'SHORT',
                'symbol': symbol,
                'shares': shares,
                'price': price,
                'value': proceeds,
                'brokerage': brokerage,
                'net_proceeds': net_proceeds,
                'pnl': 0,
                'pnl_pct': 0,
                'quantity': shares,
                'options_info': options_info
            })
    
    def execute_buy_short(self, portfolio, row, symbol, strategy=None):
        """Close a short position (buy to cover)."""
        shares = abs(portfolio['positions'].get(symbol, 0))
        if shares <= 0 or portfolio['positions'].get(symbol, 0) >= 0:
            return  # No short position to close
        
        price = float(row.get('close', 0))
        cost = shares * price
        
        # Calculate brokerage charges
        brokerage = cost * self.brokerage_rate
        total_cost = cost + brokerage
        
        portfolio['cash'] -= total_cost
        
        # Calculate P&L for short (profit when price goes down)
        entry_price = portfolio['entry_prices'].get(symbol, price)
        entry_value = entry_price * shares
        entry_brokerage = entry_value * self.brokerage_rate
        total_brokerage = entry_brokerage + brokerage
        
        # For short: profit = sell high, buy low
        pnl = entry_value - cost - total_brokerage
        pnl_pct = (pnl / (entry_value + entry_brokerage) * 100) if entry_value > 0 else 0
        
        # Get options info from strategy if available
        options_info = ""
        if strategy and hasattr(strategy, 'options_legs') and hasattr(strategy, 'trade_log') and strategy.trade_log:
            last_trade = strategy.trade_log[-1]
            legs_info = []
            for leg in last_trade.get('legs', []):
                premium = leg.get('entry_premium', 0) / 100.0  # Divide by 100 for display
                leg_str = f"{leg['strike']} {leg['type']} {leg['side']} @₹{premium:.2f}"
                legs_info.append(leg_str)
            if legs_info:
                options_info = " | ".join(legs_info)
                exit_reason = last_trade.get('exit_reason', '')
                if exit_reason:
                    options_info += f" ({exit_reason})"
        
        portfolio['positions'][symbol] = 0
        portfolio['position_types'].pop(symbol, None)
        portfolio['trades'].append({
            'date': row.get('date'),
            'action': 'BUY_SHORT',
            'trade_type': 'SHORT',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'value': cost,
            'brokerage': brokerage,
            'total_brokerage': total_brokerage,
            'total_cost': total_cost,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'quantity': shares,
            'options_info': options_info
        })

    def calculate_equity(self, portfolio, current_bar):
        equity = portfolio['cash']
        for symbol, shares in portfolio['positions'].items():
            equity += shares * float(current_bar.get('close', 0))
        return equity
    
    def calculate_equity_fast(self, portfolio, close_price):
        """Faster equity calculation using direct price value."""
        equity = portfolio['cash']
        for symbol, shares in portfolio['positions'].items():
            equity += shares * close_price
        return equity

    def calculate_metrics(self, portfolio, initial_cash):
        """Calculate comprehensive backtest metrics."""
        trades = portfolio['trades']
        equity_curve = portfolio['equity_curve']
        
        if not trades or not equity_curve:
            return {}
        
        # Separate trades by type
        closing_trades = [t for t in trades if t['action'] in ['SELL_LONG', 'BUY_SHORT', 'SELL']]
        long_trades = [t for t in trades if t.get('trade_type') == 'LONG']
        short_trades = [t for t in trades if t.get('trade_type') == 'SHORT']
        
        # Calculate P&L metrics
        total_pnl = sum(t['pnl'] for t in closing_trades)
        winning_trades = [t for t in closing_trades if t['pnl'] > 0]
        losing_trades = [t for t in closing_trades if t['pnl'] < 0]
        
        # Separate long and short closing trades
        long_closing = [t for t in closing_trades if t.get('trade_type') == 'LONG']
        short_closing = [t for t in closing_trades if t.get('trade_type') == 'SHORT']
        
        gross_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        
        # Calculate returns
        final_capital = equity_curve[-1]['equity']
        total_return_pct = ((final_capital - initial_cash) / initial_cash * 100) if initial_cash > 0 else 0
        
        # Calculate drawdown
        equity_values = [point['equity'] for point in equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        max_drawdown_peak = peak
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_peak = peak  # Track peak at max drawdown
        
        # Calculate percentage and cap at 100%
        if max_drawdown_peak > 0:
            max_drawdown_pct = min((max_drawdown / max_drawdown_peak * 100), 100.0)
        else:
            max_drawdown_pct = 0
        
        # Win rate
        total_closed_trades = len(closing_trades)
        win_rate = (len(winning_trades) / total_closed_trades * 100) if total_closed_trades > 0 else 0
        
        # Long/Short trade counts
        total_long_trades = len(long_trades)
        total_short_trades = len(short_trades)
        
        # Profit factor
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
        
        # Average win/loss
        avg_win = (gross_profit / len(winning_trades)) if winning_trades else 0
        avg_loss = (gross_loss / len(losing_trades)) if losing_trades else 0
        
        # Largest win/loss
        largest_win = max([t['pnl'] for t in winning_trades], default=0)
        largest_loss = min([t['pnl'] for t in losing_trades], default=0)
        
        # Calculate total brokerage paid
        total_brokerage = sum(t.get('brokerage', 0) for t in trades)
        
        return {
            'initial_capital': initial_cash,
            'final_capital': final_capital,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'total_trades': len(trades),
            'total_closed_trades': total_closed_trades,
            'total_long_trades': total_long_trades,
            'total_short_trades': total_short_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'total_brokerage': total_brokerage
        }
    
    def calculate_metrics_fast(self, portfolio, initial_cash, equity_values):
        """Optimized metrics calculation using numpy arrays."""
        trades = portfolio['trades']
        
        if not trades:
            return {}
        
        # Use numpy for faster calculations
        closing_trades = [t for t in trades if t['action'] in ['SELL_LONG', 'BUY_SHORT', 'SELL']]
        long_trades = [t for t in trades if t.get('trade_type') == 'LONG']
        short_trades = [t for t in trades if t.get('trade_type') == 'SHORT']
        
        if closing_trades:
            sell_pnls = np.array([t['pnl'] for t in closing_trades])
            total_pnl = sell_pnls.sum()
            winning_mask = sell_pnls > 0
            losing_mask = sell_pnls < 0
            
            winning_pnls = sell_pnls[winning_mask]
            losing_pnls = sell_pnls[losing_mask]
            
            gross_profit = winning_pnls.sum() if len(winning_pnls) > 0 else 0
            gross_loss = abs(losing_pnls.sum()) if len(losing_pnls) > 0 else 0
            
            win_rate = (winning_mask.sum() / len(sell_pnls) * 100) if len(sell_pnls) > 0 else 0
            avg_win = winning_pnls.mean() if len(winning_pnls) > 0 else 0
            avg_loss = abs(losing_pnls.mean()) if len(losing_pnls) > 0 else 0
            largest_win = winning_pnls.max() if len(winning_pnls) > 0 else 0
            largest_loss = losing_pnls.min() if len(losing_pnls) > 0 else 0
        else:
            total_pnl = 0
            gross_profit = 0
            gross_loss = 0
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            largest_win = 0
            largest_loss = 0
        
        final_capital = equity_values[-1]
        total_return_pct = ((final_capital - initial_cash) / initial_cash * 100) if initial_cash > 0 else 0
        
        # Vectorized drawdown calculation using all equity values
        equity_array = np.array(equity_values)
        # Filter out any None, zero, or negative values
        equity_array = equity_array[equity_array > 0]
        
        if len(equity_array) > 0:
            running_max = np.maximum.accumulate(equity_array)
            drawdowns = running_max - equity_array
            max_drawdown = drawdowns.max()
            max_dd_idx = drawdowns.argmax()
            # Prevent division by zero and cap unrealistic values
            if running_max[max_dd_idx] > 0:
                max_drawdown_pct = (max_drawdown / running_max[max_dd_idx] * 100)
                # Cap max drawdown percentage at 100% (can't lose more than everything)
                max_drawdown_pct = min(max_drawdown_pct, 100.0)
            else:
                max_drawdown_pct = 0
        else:
            max_drawdown = 0
            max_drawdown_pct = 0
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
        
        # Calculate total brokerage paid
        total_brokerage = sum(t.get('brokerage', 0) for t in trades)
        
        return {
            'initial_capital': initial_cash,
            'final_capital': final_capital,
            'total_pnl': float(total_pnl),
            'total_return_pct': float(total_return_pct),
            'total_trades': len(trades),
            'total_closed_trades': len(closing_trades),
            'total_long_trades': len(long_trades),
            'total_short_trades': len(short_trades),
            'winning_trades': int(np.sum(sell_pnls > 0)) if closing_trades else 0,
            'losing_trades': int(np.sum(sell_pnls < 0)) if closing_trades else 0,
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
            'total_brokerage': total_brokerage
        }
