"""
Example Moving Average Crossover Strategy

This is a simple moving average crossover strategy for demonstration purposes.
When the short-term moving average crosses above the long-term moving average, 
it generates a BUY signal. When it crosses below, it generates a SELL signal.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Moving Average Crossover Strategy
    
    Parameters:
        short_window: Period for short moving average (default: 20)
        long_window: Period for long moving average (default: 50)
    """
    
    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window
        self.position = None  # Track if we currently have a position
    
    def generate_signal(self, current_bar, historical_data):
        """
        Generate trading signal based on moving average crossover.
        
        Args:
            current_bar: Current bar data (pandas Series)
            historical_data: Historical data up to current point (pandas DataFrame)
        
        Returns:
            'BUY', 'SELL', or 'HOLD' signal
        """
        # Need enough historical data to calculate moving averages
        if len(historical_data) < self.long_window:
            return 'HOLD'
        
        # Calculate moving averages
        close_prices = historical_data['close'].values
        
        if len(close_prices) < self.long_window:
            return 'HOLD'
        
        # Short-term moving average
        short_ma = np.mean(close_prices[-self.short_window:])
        
        # Long-term moving average
        long_ma = np.mean(close_prices[-self.long_window:])
        
        # Previous short and long moving averages (for crossover detection)
        if len(close_prices) < self.long_window + 1:
            return 'HOLD'
        
        prev_short_ma = np.mean(close_prices[-(self.short_window + 1):-1])
        prev_long_ma = np.mean(close_prices[-(self.long_window + 1):-1])
        
        # Detect crossover
        # Bullish crossover: short MA crosses above long MA
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            if self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY'
        
        # Bearish crossover: short MA crosses below long MA
        elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        return 'HOLD'
