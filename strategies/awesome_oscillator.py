"""
Awesome Oscillator Strategy

This strategy uses the Awesome Oscillator which measures momentum
by comparing 5-period and 34-period simple moving averages of midpoint prices.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Awesome Oscillator Strategy
    
    Parameters:
        short_period: Short SMA period (default: 5)
        long_period: Long SMA period (default: 34)
    """
    
    def __init__(self, short_period=5, long_period=34, enable_short=True):
        self.short_period = short_period
        self.long_period = long_period
        self.enable_short = enable_short
        self.position = None
        self.prev_ao = None
    
    def calculate_midpoint(self, highs, lows):
        """Calculate midpoint prices (H+L)/2"""
        return [(highs[i] + lows[i]) / 2 for i in range(len(highs))]
    
    def calculate_ao(self, highs, lows):
        """Calculate Awesome Oscillator"""
        if len(highs) < self.long_period:
            return None
        
        midpoints = self.calculate_midpoint(highs, lows)
        
        # Calculate SMAs of midpoints
        short_sma = np.mean(midpoints[-self.short_period:])
        long_sma = np.mean(midpoints[-self.long_period:])
        
        ao = short_sma - long_sma
        return ao
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Awesome Oscillator"""
        if len(historical_data) < self.long_period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        
        # Include current bar
        current_highs = np.append(highs, current_bar['high'])
        current_lows = np.append(lows, current_bar['low'])
        
        ao = self.calculate_ao(current_highs, current_lows)
        
        if ao is None:
            return 'HOLD'
        
        # Generate signals based on AO
        
        # Zero line cross strategy
        if self.prev_ao is not None:
            # Buy: AO crosses above zero line
            if self.prev_ao <= 0 and ao > 0:
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    self.prev_ao = ao
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    self.prev_ao = ao
                    return 'BUY_LONG'
            
            # Sell: AO crosses below zero line
            elif self.prev_ao >= 0 and ao < 0:
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    self.prev_ao = ao
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    self.prev_ao = ao
                    return 'SELL_SHORT'
            
            # Twin peaks strategy (more advanced)
            # Buy: Second peak above zero lower than first, but still above zero
            elif ao > 0 and ao < self.prev_ao:
                # Look for divergence with price for more sophisticated signal
                pass
        
        self.prev_ao = ao
        return 'HOLD'