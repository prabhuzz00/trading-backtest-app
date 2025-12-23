"""
Range Breakout Strategy

This strategy identifies consolidation ranges and trades breakouts
from these ranges, expecting continuation of the breakout direction.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Range Breakout Strategy
    
    Parameters:
        range_period: Period to identify range (default: 20)
        min_consolidation: Minimum consolidation periods (default: 10)
        breakout_threshold: Percentage breakout threshold (default: 1.0)
    """
    
    def __init__(self, range_period=20, min_consolidation=10, breakout_threshold=1.0, enable_short=True):
        self.range_period = range_period
        self.min_consolidation = min_consolidation
        self.breakout_threshold = breakout_threshold
        self.enable_short = enable_short
        self.position = None
        self.consolidation_count = 0
        self.range_high = None
        self.range_low = None
    
    def identify_range(self, highs, lows, closes):
        """Identify current trading range"""
        if len(closes) < self.range_period:
            return None, None
        
        recent_highs = highs[-self.range_period:]
        recent_lows = lows[-self.range_period:]
        
        range_high = np.max(recent_highs)
        range_low = np.min(recent_lows)
        
        return range_high, range_low
    
    def is_consolidating(self, range_high, range_low, current_high, current_low):
        """Check if price is consolidating within range"""
        if range_high is None or range_low is None:
            return False
        
        range_size = range_high - range_low
        if range_size == 0:
            return False
        
        # Check if current bar is within the range
        within_range = (current_low >= range_low and current_high <= range_high)
        
        return within_range
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on range breakouts"""
        if len(historical_data) < self.range_period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Identify current range
        current_range_high, current_range_low = self.identify_range(highs, lows, closes)
        
        if current_range_high is None or current_range_low is None:
            return 'HOLD'
        
        # Update range if significantly different
        if (self.range_high is None or 
            abs(current_range_high - self.range_high) / self.range_high > 0.05):
            self.range_high = current_range_high
            self.range_low = current_range_low
            self.consolidation_count = 0
        
        # Check if currently consolidating
        is_consolidating = self.is_consolidating(
            self.range_high, self.range_low, current_high, current_low)
        
        if is_consolidating:
            self.consolidation_count += 1
        else:
            # Reset consolidation count if breakout occurs
            if self.consolidation_count >= self.min_consolidation:
                # We have sufficient consolidation, check for breakout
                
                range_size = self.range_high - self.range_low
                breakout_distance = range_size * (self.breakout_threshold / 100)
                
                # Upward breakout
                if current_high > self.range_high + breakout_distance:
                    if self.position == 'SHORT':
                        # Close short position
                        self.position = None
                        self.consolidation_count = 0
                        return 'BUY_SHORT'
                    elif self.position != 'LONG':
                        # Open long position
                        self.position = 'LONG'
                        self.consolidation_count = 0
                        return 'BUY_LONG'
                
                # Downward breakout
                elif current_low < self.range_low - breakout_distance:
                    if self.position == 'LONG':
                        # Close long position
                        self.position = None
                        self.consolidation_count = 0
                        return 'SELL_LONG'
                    elif self.position != 'SHORT' and self.enable_short:
                        # Open short position
                        self.position = 'SHORT'
                        self.consolidation_count = 0
                        return 'SELL_SHORT'
            
            # Reset consolidation count for failed breakout
            self.consolidation_count = 0
        
        # Exit conditions
        if self.position == 'LONG':
            # Exit if price returns back into the range
            if current_close < self.range_high:
                self.position = None
                return 'SELL_LONG'
        
        elif self.position == 'SHORT':
            # Exit if price returns back into the range
            if current_close > self.range_low:
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'