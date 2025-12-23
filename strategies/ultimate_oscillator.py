"""
Ultimate Oscillator Strategy

This strategy uses Ultimate Oscillator which combines momentum across
three different time periods (7, 14, 28) to reduce false signals.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Ultimate Oscillator Strategy
    
    Parameters:
        short_period: Short period (default: 7)
        medium_period: Medium period (default: 14)
        long_period: Long period (default: 28)
        overbought_level: Overbought threshold (default: 70)
        oversold_level: Oversold threshold (default: 30)
    """
    
    def __init__(self, short_period=7, medium_period=14, long_period=28, 
                 overbought_level=70, oversold_level=30, enable_short=True):
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.enable_short = enable_short
        self.position = None
    
    def calculate_true_range(self, high, low, prev_close):
        """Calculate True Range"""
        high_low = high - low
        high_prev_close = abs(high - prev_close)
        low_prev_close = abs(low - prev_close)
        return max(high_low, high_prev_close, low_prev_close)
    
    def calculate_buying_pressure(self, close, low, prev_close):
        """Calculate Buying Pressure"""
        true_low = min(low, prev_close)
        return close - true_low
    
    def calculate_ultimate_oscillator(self, highs, lows, closes):
        """Calculate Ultimate Oscillator"""
        if len(closes) < self.long_period + 1:
            return None
        
        # Calculate buying pressure and true range for each period
        buying_pressures = []
        true_ranges = []
        
        for i in range(1, len(closes)):
            bp = self.calculate_buying_pressure(closes[i], lows[i], closes[i-1])
            tr = self.calculate_true_range(highs[i], lows[i], closes[i-1])
            buying_pressures.append(bp)
            true_ranges.append(tr)
        
        if len(buying_pressures) < self.long_period:
            return None
        
        # Calculate averages for each period
        def calculate_average(data, period):
            if len(data) < period:
                return 0
            return sum(data[-period:])
        
        # Short period average
        bp_short = calculate_average(buying_pressures, self.short_period)
        tr_short = calculate_average(true_ranges, self.short_period)
        
        # Medium period average
        bp_medium = calculate_average(buying_pressures, self.medium_period)
        tr_medium = calculate_average(true_ranges, self.medium_period)
        
        # Long period average
        bp_long = calculate_average(buying_pressures, self.long_period)
        tr_long = calculate_average(true_ranges, self.long_period)
        
        # Calculate raw values
        if tr_short == 0 or tr_medium == 0 or tr_long == 0:
            return 50  # Return neutral value
        
        raw_short = bp_short / tr_short
        raw_medium = bp_medium / tr_medium
        raw_long = bp_long / tr_long
        
        # Calculate Ultimate Oscillator
        uo = 100 * ((4 * raw_short) + (2 * raw_medium) + raw_long) / (4 + 2 + 1)
        
        return uo
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Ultimate Oscillator"""
        if len(historical_data) < self.long_period + 2:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        # Include current bar
        current_highs = np.append(highs, current_bar['high'])
        current_lows = np.append(lows, current_bar['low'])
        current_closes = np.append(closes, current_bar['close'])
        
        uo = self.calculate_ultimate_oscillator(current_highs, current_lows, current_closes)
        
        if uo is None:
            return 'HOLD'
        
        # Generate signals
        
        # Buy: Ultimate Oscillator oversold
        if uo <= self.oversold_level:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: Ultimate Oscillator overbought
        elif uo >= self.overbought_level:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'