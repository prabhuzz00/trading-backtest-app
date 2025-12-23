"""
Williams %R Strategy

This strategy uses Williams %R oscillator to identify overbought and oversold
conditions. It's similar to Stochastic but ranges from 0 to -100.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Williams %R Strategy
    
    Parameters:
        period: Lookback period (default: 14)
        oversold: Oversold threshold (default: -80)
        overbought: Overbought threshold (default: -20)
    """
    
    def __init__(self, period=14, oversold=-80, overbought=-20, enable_short=True):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.enable_short = enable_short
        self.position = None
    
    def calculate_williams_r(self, highs, lows, closes):
        """Calculate Williams %R"""
        if len(closes) < self.period:
            return None
        
        highest_high = np.max(highs[-self.period:])
        lowest_low = np.min(lows[-self.period:])
        current_close = closes[-1]
        
        if highest_high == lowest_low:
            return -50  # Avoid division by zero
        
        williams_r = ((highest_high - current_close) / (highest_high - lowest_low)) * -100
        
        return williams_r
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Williams %R"""
        if len(historical_data) < self.period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        williams_r = self.calculate_williams_r(highs, lows, closes)
        
        if williams_r is None:
            return 'HOLD'
        
        # Buy signal when oversold (Williams %R < -80)
        if williams_r <= self.oversold:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell signal when overbought (Williams %R > -20)
        elif williams_r >= self.overbought:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'