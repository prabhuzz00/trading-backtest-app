"""
Z-Score Mean Reversion Strategy

This strategy calculates the z-score of the current price relative to its
rolling mean and standard deviation, trading when price deviates significantly.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Z-Score Mean Reversion Strategy
    
    Parameters:
        lookback_period: Period for mean and std calculation (default: 20)
        entry_threshold: Z-score threshold for entry (default: 2.0)
        exit_threshold: Z-score threshold for exit (default: 0.5)
    """
    
    def __init__(self, lookback_period=20, entry_threshold=2.0, exit_threshold=0.5, enable_short=True):
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.enable_short = enable_short
        self.position = None
    
    def calculate_zscore(self, current_price, prices):
        """Calculate z-score of current price"""
        if len(prices) < self.lookback_period:
            return 0
        
        recent_prices = prices[-self.lookback_period:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        
        if std_price == 0:
            return 0
        
        zscore = (current_price - mean_price) / std_price
        return zscore
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on price z-score"""
        if len(historical_data) < self.lookback_period:
            return 'HOLD'
        
        current_price = current_bar['close']
        historical_prices = historical_data['close'].values
        
        # Calculate z-score
        zscore = self.calculate_zscore(current_price, historical_prices)
        
        # Entry signals (price significantly deviates from mean)
        if zscore <= -self.entry_threshold:
            # Price significantly below mean (oversold)
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        elif zscore >= self.entry_threshold:
            # Price significantly above mean (overbought)
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit signals (price returns closer to mean)
        elif abs(zscore) <= self.exit_threshold:
            if self.position == 'LONG':
                self.position = None
                return 'SELL_LONG'
            elif self.position == 'SHORT':
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'