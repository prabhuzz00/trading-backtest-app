import pandas as pd
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
            'equity_curve': []
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

        metrics = {}  # stub, compute metrics in reports/metrics.py
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
            portfolio['trades'].append({
                'date': row.get('date'),
                'action': 'BUY',
                'symbol': symbol,
                'shares': shares,
                'price': price
            })

    def execute_sell(self, portfolio, row, symbol):
        shares = portfolio['positions'].get(symbol, 0)
        if shares <= 0:
            return
        price = float(row.get('close', 0))
        proceeds = shares * price
        portfolio['cash'] += proceeds
        portfolio['positions'][symbol] = 0
        portfolio['trades'].append({
            'date': row.get('date'),
            'action': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': price
        })

    def calculate_equity(self, portfolio, current_bar):
        equity = portfolio['cash']
        for symbol, shares in portfolio['positions'].items():
            equity += shares * float(current_bar.get('close', 0))
        return equity
