"""
Bollinger Bands Strategy with Long & Short

This strategy uses Bollinger Bands for mean reversion.
- Long: Buy at lower band, sell at middle/upper band
- Short: Sell short at upper band, cover at middle/lower band
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Bollinger Bands Strategy with Long and Short trading
    
    Parameters:
        period: Period for moving average (default: 20)
        std_dev: Number of standard deviations (default: 2)
        enable_short: Enable short trading (default: True)
    """
    
    def __init__(self, period=20, std_dev=2, enable_short=True):
        self.period = period
        self.std_dev = std_dev
        self.enable_short = enable_short
        self.position = None
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Bollinger Bands"""
        if len(historical_data) < self.period:
            return 'HOLD'
        
        close_prices = historical_data['close'].values[-self.period:]
        current_price = current_bar['close']
        
        # Calculate Bollinger Bands
        middle_band = np.mean(close_prices)  # SMA
        std = np.std(close_prices)
        upper_band = middle_band + (self.std_dev * std)
        lower_band = middle_band - (self.std_dev * std)
        
        # Mean reversion signals
        # Long entry: price touches or goes below lower band
        if current_price <= lower_band:
            if self.position == 'SHORT':
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Short entry: price touches or goes above upper band
        elif current_price >= upper_band:
            if self.position == 'LONG':
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit at middle band
        elif current_price >= middle_band and current_price < upper_band:
            if self.position == 'LONG':
                self.position = None
                return 'SELL_LONG'
        elif current_price <= middle_band and current_price > lower_band:
            if self.position == 'SHORT':
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'