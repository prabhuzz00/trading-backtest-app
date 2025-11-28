import pandas as pd
import numpy as np
from utils.db_connection import get_stock_data
from engine.strategy_loader import load_strategy

class BacktestEngine:
    def __init__(self, initial_cash=100000):
        self.initial_cash = initial_cash

    def run_backtest(self, strategy_path, stock_symbol, start_date, end_date):
        data = get_stock_data(stock_symbol, start_date, end_date)
        if data is None or data.empty:
            raise ValueError("No data returned for symbol/date range")

        strategy = load_strategy(strategy_path)

        portfolio = {
            'cash': self.initial_cash,
            'positions': {},
            'trades': [],
            'equity_curve': [],
            'buy_prices': {}  # Track buy prices for P&L calculation
        }

        for index, row in data.iterrows():
            signal = strategy.generate_signal(row, data.loc[:index])
            if signal == 'BUY':
                self.execute_buy(portfolio, row, stock_symbol)
            elif signal == 'SELL':
                self.execute_sell(portfolio, row, stock_symbol)

            equity = self.calculate_equity(portfolio, row)
            portfolio['equity_curve'].append({
                'date': row.get('date', index),
                'equity': equity
            })

        # Calculate comprehensive metrics
        metrics = self.calculate_metrics(portfolio, self.initial_cash)
        
        return {
            'trades': portfolio['trades'],
            'equity_curve': portfolio['equity_curve'],
            'metrics': metrics
        }

    def execute_buy(self, portfolio, row, symbol):
        price = float(row.get('close', 0))
        if price <= 0:
            return
        shares = int(portfolio['cash'] * 0.95 / price)
        cost = shares * price
        if shares > 0:
            portfolio['cash'] -= cost
            portfolio['positions'][symbol] = portfolio['positions'].get(symbol, 0) + shares
            portfolio['buy_prices'][symbol] = price  # Store buy price for P&L calculation
            portfolio['trades'].append({
                'date': row.get('date'),
                'action': 'BUY',
                'symbol': symbol,
                'shares': shares,
                'price': price,
                'value': cost,
                'pnl': 0,
                'pnl_pct': 0
            })

    def execute_sell(self, portfolio, row, symbol):
        shares = portfolio['positions'].get(symbol, 0)
        if shares <= 0:
            return
        price = float(row.get('close', 0))
        proceeds = shares * price
        portfolio['cash'] += proceeds
        
        # Calculate P&L
        buy_price = portfolio['buy_prices'].get(symbol, price)
        pnl = (price - buy_price) * shares
        pnl_pct = ((price - buy_price) / buy_price * 100) if buy_price > 0 else 0
        
        portfolio['positions'][symbol] = 0
        portfolio['trades'].append({
            'date': row.get('date'),
            'action': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'value': proceeds,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })

    def calculate_equity(self, portfolio, current_bar):
        equity = portfolio['cash']
        for symbol, shares in portfolio['positions'].items():
            equity += shares * float(current_bar.get('close', 0))
        return equity

    def calculate_metrics(self, portfolio, initial_cash):
        """Calculate comprehensive backtest metrics."""
        trades = portfolio['trades']
        equity_curve = portfolio['equity_curve']
        
        if not trades or not equity_curve:
            return {}
        
        # Separate buy and sell trades
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        
        # Calculate P&L metrics
        total_pnl = sum(t['pnl'] for t in sell_trades)
        winning_trades = [t for t in sell_trades if t['pnl'] > 0]
        losing_trades = [t for t in sell_trades if t['pnl'] < 0]
        
        gross_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        
        # Calculate returns
        final_capital = equity_curve[-1]['equity']
        total_return_pct = ((final_capital - initial_cash) / initial_cash * 100) if initial_cash > 0 else 0
        
        # Calculate drawdown
        equity_values = [point['equity'] for point in equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else 0
        
        # Win rate
        total_closed_trades = len(sell_trades)
        win_rate = (len(winning_trades) / total_closed_trades * 100) if total_closed_trades > 0 else 0
        
        # Profit factor
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
        
        # Average win/loss
        avg_win = (gross_profit / len(winning_trades)) if winning_trades else 0
        avg_loss = (gross_loss / len(losing_trades)) if losing_trades else 0
        
        # Largest win/loss
        largest_win = max([t['pnl'] for t in winning_trades], default=0)
        largest_loss = min([t['pnl'] for t in losing_trades], default=0)
        
        return {
            'initial_capital': initial_cash,
            'final_capital': final_capital,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'total_trades': len(trades),
            'total_closed_trades': total_closed_trades,
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
            'max_drawdown_pct': max_drawdown_pct
        }
