"""
Moving Average Crossover Strategy (LONG & SHORT)

This strategy supports both long and short trading.
- Long: Buy when short MA crosses above long MA, Sell when crosses below
- Short: Sell short when short MA crosses below long MA, Cover when crosses above
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Moving Average Crossover Strategy with Long and Short trading
    
    Parameters:
        short_window: Period for short moving average (default: 20)
        long_window: Period for long moving average (default: 50)
        enable_short: Enable short trading (default: True)
    """
    
    def __init__(self, short_window=20, long_window=50, enable_short=True):
        self.short_window = short_window
        self.long_window = long_window
        self.enable_short = enable_short
        self.position = None  # Track if we currently have a position: 'LONG', 'SHORT', or None
    
    def generate_signal(self, current_bar, historical_data):
        """
        Generate trading signal based on moving average crossover.
        
        Args:
            current_bar: Current bar data (pandas Series)
            historical_data: Historical data up to current point (pandas DataFrame)
        
        Returns:
            'BUY_LONG', 'SELL_LONG', 'SELL_SHORT', 'BUY_SHORT', or 'HOLD' signal
        """
        # Need enough historical data to calculate moving averages
        if len(historical_data) < self.long_window + 1:
            return 'HOLD'
        
        # Calculate moving averages
        close_prices = historical_data['close'].values
        
        if len(close_prices) < self.long_window + 1:
            return 'HOLD'
        
        # Short-term moving average
        short_ma = np.mean(close_prices[-self.short_window:])
        
        # Long-term moving average
        long_ma = np.mean(close_prices[-self.long_window:])
        
        # Previous short and long moving averages (for crossover detection)
        prev_short_ma = np.mean(close_prices[-(self.short_window + 1):-1])
        prev_long_ma = np.mean(close_prices[-(self.long_window + 1):-1])
        
        # Detect crossover
        # Bullish crossover: short MA crosses above long MA
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Bearish crossover: short MA crosses below long MA
        elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'
