"""
Rate of Change (ROC) Strategy

This strategy uses Rate of Change indicator to measure momentum
by comparing current price to price n periods ago.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Rate of Change Momentum Strategy
    
    Parameters:
        roc_period: ROC calculation period (default: 12)
        roc_threshold: ROC threshold for signals (default: 5.0)
        ma_period: Moving average filter period (default: 20)
    """
    
    def __init__(self, roc_period=12, roc_threshold=5.0, ma_period=20, enable_short=True):
        self.roc_period = roc_period
        self.roc_threshold = roc_threshold
        self.ma_period = ma_period
        self.enable_short = enable_short
        self.position = None
    
    def calculate_roc(self, prices):
        """Calculate Rate of Change"""
        if len(prices) < self.roc_period + 1:
            return None
        
        current_price = prices[-1]
        past_price = prices[-self.roc_period - 1]
        
        if past_price == 0:
            return 0
        
        roc = ((current_price - past_price) / past_price) * 100
        return roc
    
    def calculate_moving_average(self, prices):
        """Calculate simple moving average"""
        if len(prices) < self.ma_period:
            return None
        
        return np.mean(prices[-self.ma_period:])
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on ROC momentum"""
        if len(historical_data) < max(self.roc_period + 1, self.ma_period):
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_price = current_bar['close']
        
        # Calculate ROC
        roc = self.calculate_roc(closes)
        
        if roc is None:
            return 'HOLD'
        
        # Calculate moving average for trend filter
        ma_value = self.calculate_moving_average(closes)
        
        if ma_value is None:
            return 'HOLD'
        
        # ROC momentum signals with trend filter
        
        # Buy: Strong positive ROC above threshold and price above MA
        if roc >= self.roc_threshold and current_price > ma_value:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: Strong negative ROC below threshold and price below MA
        elif roc <= -self.roc_threshold and current_price < ma_value:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit on reversal
        elif self.position == 'LONG' and (roc <= -self.roc_threshold or current_price < ma_value):
            self.position = None
            return 'SELL_LONG'
        
        elif self.position == 'SHORT' and (roc >= self.roc_threshold or current_price > ma_value):
            self.position = None
            return 'BUY_SHORT'
        
        return 'HOLD'