"""
Donchian Channels Strategy

This strategy uses Donchian Channels which plot the highest high and lowest low
over a specified period. Buy on breakout above upper channel, sell on breakdown
below lower channel.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Donchian Channels Strategy
    
    Parameters:
        period: Channel period (default: 20)
        exit_period: Exit channel period (default: 10)
    """
    
    def __init__(self, period=20, exit_period=10, enable_short=True):
        self.period = period
        self.exit_period = exit_period
        self.enable_short = enable_short
        self.position = None
    
    def calculate_donchian_channels(self, highs, lows, period):
        """Calculate Donchian Channel upper and lower bands"""
        if len(highs) < period:
            return None, None
        
        upper_channel = np.max(highs[-period:])
        lower_channel = np.min(lows[-period:])
        
        return upper_channel, lower_channel
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Donchian Channel breakouts"""
        if len(historical_data) < self.period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Calculate entry channels
        upper_channel, lower_channel = self.calculate_donchian_channels(
            highs[:-1], lows[:-1], self.period)  # Exclude current bar
        
        if upper_channel is None:
            return 'HOLD'
        
        # Calculate exit channels
        exit_upper, exit_lower = self.calculate_donchian_channels(
            highs[:-1], lows[:-1], self.exit_period)
        
        # Entry signals
        # Buy on breakout above upper channel
        if current_high > upper_channel:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell on breakdown below lower channel
        elif current_low < lower_channel and self.enable_short:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT':
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit signals
        if self.position == 'LONG':
            # Exit on breakdown below exit lower channel
            if exit_lower is not None and current_low < exit_lower:
                self.position = None
                return 'SELL_LONG'
        
        elif self.position == 'SHORT':
            # Exit on breakout above exit upper channel
            if exit_upper is not None and current_high > exit_upper:
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'