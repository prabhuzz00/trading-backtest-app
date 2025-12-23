"""
OHLC Chart Widget with Trade Indicators

This widget displays candlestick charts with buy/sell trade markers.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QPushButton
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np

class OHLCChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.price_data = None
        self.trades = []
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Chart type selector
        control_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Candlestick", "OHLC Bars", "Line"])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart)
        control_layout.addWidget(self.chart_type_combo)
        
        # Show trades toggle
        self.show_trades_btn = QPushButton("Hide Trades")
        self.show_trades_btn.setCheckable(True)
        self.show_trades_btn.setChecked(False)
        self.show_trades_btn.clicked.connect(self.toggle_trades)
        control_layout.addWidget(self.show_trades_btn)
        
        # Show volume toggle
        self.show_volume_btn = QPushButton("Show Volume")
        self.show_volume_btn.setCheckable(True)
        self.show_volume_btn.setChecked(False)
        self.show_volume_btn.clicked.connect(self.update_chart)
        control_layout.addWidget(self.show_volume_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Create matplotlib figure with better default settings
        self.figure = Figure(figsize=(12, 8), dpi=100)
        # Enable tight layout by default
        self.figure.set_tight_layout(True)
        self.canvas = FigureCanvas(self.figure)
        # Enable antialiasing for better performance
        self.canvas.setStyleSheet("background-color: white;")
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Status label
        self.status_label = QLabel("Run a backtest to see OHLC chart with trade indicators")
        layout.addWidget(self.status_label)
    
    def plot_ohlc_with_trades(self, price_data, trades):
        """
        Plot OHLC chart with buy/sell trade markers.
        Optimized for large datasets.
        
        Args:
            price_data: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
            trades: list of dicts with trade information
        """
        if price_data is None or price_data.empty:
            self.status_label.setText("No price data available")
            return
        
        # Store full data but downsample for display
        # Downsample more aggressively for very large datasets
        if len(price_data) > 5000:
            step = len(price_data) // 1000
            self.price_data = price_data.iloc[::step].copy()
        elif len(price_data) > 2000:
            step = len(price_data) // 1500
            self.price_data = price_data.iloc[::step].copy()
        else:
            self.price_data = price_data.copy()
        
        self.trades = trades
        
        # Ensure date column is datetime
        if 'date' in self.price_data.columns:
            self.price_data['date'] = pd.to_datetime(self.price_data['date'])
        
        self.update_chart()
    
    def update_chart(self):
        """Update the chart based on current settings"""
        if self.price_data is None or self.price_data.empty:
            return
        
        # Clear previous plot efficiently
        self.figure.clear()
        
        # Limit data points for better performance
        max_candles = 500
        data_to_plot = self.price_data
        if len(data_to_plot) > max_candles:
            # Show last 500 candles
            data_to_plot = self.price_data.iloc[-max_candles:].copy()
        
        # Determine if we need volume subplot
        show_volume = self.show_volume_btn.isChecked() and 'volume' in data_to_plot.columns
        
        if show_volume:
            # Create subplots: price chart and volume
            ax_price = self.figure.add_subplot(211)
            ax_volume = self.figure.add_subplot(212, sharex=ax_price)
        else:
            ax_price = self.figure.add_subplot(111)
            ax_volume = None
        
        # Update data reference for plotting
        self.plot_data = data_to_plot
        
        # Plot based on chart type
        chart_type = self.chart_type_combo.currentText()
        
        if chart_type == "Candlestick":
            self.plot_candlestick(ax_price)
        elif chart_type == "OHLC Bars":
            self.plot_ohlc_bars(ax_price)
        else:  # Line
            self.plot_line(ax_price)
        
        # Plot trades if not hidden
        if not self.show_trades_btn.isChecked():
            self.plot_trade_markers(ax_price)
        
        # Plot volume if enabled
        if show_volume and ax_volume is not None:
            self.plot_volume(ax_volume)
        
        # Format the plot
        ax_price.set_ylabel('Price (₹)', fontsize=10)
        ax_price.set_title('Price Chart with Trade Signals', fontsize=12, fontweight='bold')
        ax_price.grid(True, alpha=0.3)
        ax_price.legend(loc='upper left')
        
        # Format x-axis
        if ax_volume is not None:
            ax_volume.set_xlabel('Date', fontsize=10)
        else:
            ax_price.set_xlabel('Date', fontsize=10)
        
        # Format dates on x-axis
        ax_price.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax_price.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()
        
        # Tight layout
        self.figure.tight_layout(pad=1.0)
        
        # Update canvas with draw_idle for better performance
        self.canvas.draw_idle()
        
        # Update status
        self.update_status()
    
    def plot_candlestick(self, ax):
        """Plot candlestick chart using vectorized operations for better performance"""
        data = self.plot_data if hasattr(self, 'plot_data') else self.price_data
        
        # Calculate width for candlesticks
        if len(data) > 1:
            # Calculate average time difference
            time_diffs = [(data['date'].iloc[i+1] - data['date'].iloc[i]).days 
                         for i in range(min(10, len(data)-1))]
            avg_diff = np.mean(time_diffs) if time_diffs else 1
            width = avg_diff * 0.6
        else:
            width = 0.6
        
        # Convert dates to matplotlib date numbers once
        date_nums = mdates.date2num(data['date'].values)
        
        # Vectorize color determination
        is_bullish = data['close'].values >= data['open'].values
        
        # Plot high-low lines in batches for better performance
        for i, (date_num, is_bull) in enumerate(zip(date_nums, is_bullish)):
            row = data.iloc[i]
            color = '#26a69a' if is_bull else '#ef5350'
            
            # Draw high-low line
            ax.plot([date_num, date_num], [row['low'], row['high']], 
                   color=color, linewidth=1, zorder=1)
            
            # Draw body rectangle
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['open'], row['close'])
            
            rect = Rectangle((date_num - width/2, body_bottom), width, body_height,
                           facecolor=color, edgecolor=color, linewidth=0.5, zorder=2)
            ax.add_patch(rect)
        
        # Set limits
        ax.set_xlim(date_nums[0] - 1, date_nums[-1] + 1)
    
    def plot_ohlc_bars(self, ax):
        """Plot OHLC bar chart with optimized rendering"""
        data = self.plot_data if hasattr(self, 'plot_data') else self.price_data
        
        # Calculate width for bars
        if len(data) > 1:
            time_diffs = [(data['date'].iloc[i+1] - data['date'].iloc[i]).days 
                         for i in range(min(10, len(data)-1))]
            avg_diff = np.mean(time_diffs) if time_diffs else 1
            width = avg_diff * 0.3
        else:
            width = 0.3
        
        # Convert dates once
        date_nums = mdates.date2num(data['date'].values)
        is_bullish = data['close'].values >= data['open'].values
        
        # Plot OHLC bars
        for i, (date_num, is_bull) in enumerate(zip(date_nums, is_bullish)):
            row = data.iloc[i]
            color = '#26a69a' if is_bull else '#ef5350'
            
            # Draw vertical line (high-low)
            ax.plot([date_num, date_num], [row['low'], row['high']], 
                   color=color, linewidth=1.5, zorder=1)
            
            # Draw open tick (left)
            ax.plot([date_num - width, date_num], [row['open'], row['open']], 
                   color=color, linewidth=1.5, zorder=2)
            
            # Draw close tick (right)
            ax.plot([date_num, date_num + width], [row['close'], row['close']], 
                   color=color, linewidth=1.5, zorder=2)
    
    def plot_line(self, ax):
        """Plot simple line chart with optimized rendering"""
        data = self.plot_data if hasattr(self, 'plot_data') else self.price_data
        # Use numpy arrays directly for faster plotting
        dates = mdates.date2num(data['date'].values)
        closes = data['close'].values
        
        ax.plot(dates, closes, linewidth=1.5, color='#2E86AB', label='Close Price', antialiased=True)
    
    def plot_trade_markers(self, ax):
        """Plot buy and sell trade markers"""
        if not self.trades:
            return
        
        buy_trades = [t for t in self.trades if t.get('action') == 'BUY']
        sell_trades = [t for t in self.trades if t.get('action') == 'SELL']
        
        # Plot buy markers
        if buy_trades:
            buy_dates = [mdates.date2num(pd.to_datetime(t['date'])) for t in buy_trades]
            buy_prices = [t['price'] for t in buy_trades]
            ax.scatter(buy_dates, buy_prices, marker='^', s=150, c='#00ff00', 
                      edgecolors='darkgreen', linewidth=2, zorder=10, label='Buy', alpha=0.8)
        
        # Plot sell markers
        if sell_trades:
            sell_dates = [mdates.date2num(pd.to_datetime(t['date'])) for t in sell_trades]
            sell_prices = [t['price'] for t in sell_trades]
            ax.scatter(sell_dates, sell_prices, marker='v', s=150, c='#ff0000', 
                      edgecolors='darkred', linewidth=2, zorder=10, label='Sell', alpha=0.8)
    
    def plot_volume(self, ax):
        """Plot volume bars"""
        data = self.plot_data if hasattr(self, 'plot_data') else self.price_data
        
        if 'volume' not in data.columns:
            return
        
        # Calculate width for volume bars
        if len(data) > 1:
            time_diffs = [(data['date'].iloc[i+1] - data['date'].iloc[i]).days 
                         for i in range(min(10, len(data)-1))]
            avg_diff = np.mean(time_diffs) if time_diffs else 1
            width = avg_diff * 0.8
        else:
            width = 0.8
        
        # Plot volume bars
        colors = ['#26a69a' if data.iloc[i]['close'] >= data.iloc[i]['open'] else '#ef5350' 
                 for i in range(len(data))]
        
        dates = [mdates.date2num(d) for d in data['date']]
        ax.bar(dates, data['volume'], width=width, color=colors, alpha=0.5, zorder=1)
        
        ax.set_ylabel('Volume', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format volume numbers
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'))
    
    def toggle_trades(self):
        """Toggle trade markers visibility"""
        if self.show_trades_btn.isChecked():
            self.show_trades_btn.setText("Show Trades")
        else:
            self.show_trades_btn.setText("Hide Trades")
        self.update_chart()
    
    def update_status(self):
        """Update status label with chart information"""
        if self.price_data is None or self.price_data.empty:
            return
        
        num_bars = len(self.price_data)
        num_trades = len(self.trades)
        buy_trades = len([t for t in self.trades if t.get('action') == 'BUY'])
        sell_trades = len([t for t in self.trades if t.get('action') == 'SELL'])
        
        start_date = self.price_data['date'].iloc[0].strftime('%Y-%m-%d')
        end_date = self.price_data['date'].iloc[-1].strftime('%Y-%m-%d')
        
        first_close = self.price_data['close'].iloc[0]
        last_close = self.price_data['close'].iloc[-1]
        price_change = last_close - first_close
        price_change_pct = (price_change / first_close * 100) if first_close > 0 else 0
        
        self.status_label.setText(
            f"Period: {start_date} to {end_date} | "
            f"Bars: {num_bars} | "
            f"Trades: {num_trades} (Buy: {buy_trades}, Sell: {sell_trades}) | "
            f"Price Change: ₹{price_change:+.2f} ({price_change_pct:+.2f}%)"
        )
