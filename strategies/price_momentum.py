"""
Price Momentum Strategy

This strategy identifies and trades in the direction of price momentum
using rate of change and moving average filters.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Price Momentum Strategy
    
    Parameters:
        momentum_period: Period for momentum calculation (default: 10)
        ma_period: Moving average filter period (default: 20)
        momentum_threshold: Minimum momentum % for signal (default: 2.0)
    """
    
    def __init__(self, momentum_period=10, ma_period=20, momentum_threshold=2.0, enable_short=True):
        self.momentum_period = momentum_period
        self.ma_period = ma_period
        self.momentum_threshold = momentum_threshold
        self.enable_short = enable_short
        self.position = None
    
    def calculate_momentum(self, prices):
        """Calculate price momentum (rate of change)"""
        if len(prices) < self.momentum_period + 1:
            return 0
        
        current_price = prices[-1]
        past_price = prices[-self.momentum_period - 1]
        
        if past_price == 0:
            return 0
        
        momentum = ((current_price - past_price) / past_price) * 100
        return momentum
    
    def calculate_moving_average(self, prices):
        """Calculate simple moving average"""
        if len(prices) < self.ma_period:
            return None
        
        return np.mean(prices[-self.ma_period:])
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on momentum"""
        if len(historical_data) < max(self.momentum_period + 1, self.ma_period):
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_price = current_bar['close']
        
        # Calculate momentum
        momentum = self.calculate_momentum(closes)
        
        # Calculate moving average for trend filter
        ma_value = self.calculate_moving_average(closes)
        
        if ma_value is None:
            return 'HOLD'
        
        # Momentum signals with trend filter
        
        # Buy: Strong positive momentum above moving average
        if (momentum >= self.momentum_threshold and current_price > ma_value):
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: Strong negative momentum below moving average
        elif (momentum <= -self.momentum_threshold and current_price < ma_value):
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit on momentum reversal
        elif self.position == 'LONG' and (momentum < 0 or current_price < ma_value):
            self.position = None
            return 'SELL_LONG'
        
        elif self.position == 'SHORT' and (momentum > 0 or current_price > ma_value):
            self.position = None
            return 'BUY_SHORT'
        
        return 'HOLD'