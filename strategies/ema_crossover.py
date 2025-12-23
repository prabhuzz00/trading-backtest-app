"""
Exponential Moving Average (EMA) Crossover Strategy with Long & Short

This strategy uses two exponential moving averages.
- Long: Fast EMA crosses above slow EMA
- Short: Fast EMA crosses below slow EMA
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    EMA Crossover Strategy with Long and Short trading
    
    Parameters:
        fast_period: Period for fast EMA (default: 12)
        slow_period: Period for slow EMA (default: 26)
        enable_short: Enable short trading (default: True)
    """
    
    def __init__(self, fast_period=12, slow_period=26, enable_short=True):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.enable_short = enable_short
        self.position = None
        self.prev_fast_ema = None
        self.prev_slow_ema = None
    
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on EMA crossover"""
        if len(historical_data) < self.slow_period:
            return 'HOLD'
        
        close_prices = historical_data['close'].values
        
        # Calculate current EMAs
        fast_ema = self.calculate_ema(close_prices, self.fast_period)
        slow_ema = self.calculate_ema(close_prices, self.slow_period)
        
        if fast_ema is None or slow_ema is None:
            return 'HOLD'
        
        # Check for crossover
        signal = 'HOLD'
        if self.prev_fast_ema is not None and self.prev_slow_ema is not None:
            # Bullish crossover - fast crosses above slow
            if self.prev_fast_ema <= self.prev_slow_ema and fast_ema > slow_ema:
                if self.position == 'SHORT':
                    self.position = None
                    signal = 'BUY_SHORT'
                elif self.position != 'LONG':
                    self.position = 'LONG'
                    signal = 'BUY_LONG'
            
            # Bearish crossover - fast crosses below slow
            elif self.prev_fast_ema >= self.prev_slow_ema and fast_ema < slow_ema:
                if self.position == 'LONG':
                    self.position = None
                    signal = 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    self.position = 'SHORT'
                    signal = 'SELL_SHORT'
        
        self.prev_fast_ema = fast_ema
        self.prev_slow_ema = slow_ema
        return signal