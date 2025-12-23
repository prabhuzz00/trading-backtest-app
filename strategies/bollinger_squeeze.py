"""
Bollinger Band Squeeze Strategy

This strategy identifies periods when Bollinger Bands contract (squeeze)
and trades the subsequent volatility expansion breakout.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Bollinger Band Squeeze Strategy
    
    Parameters:
        bb_period: Bollinger Bands period (default: 20)
        bb_std: Bollinger Bands standard deviation (default: 2.0)
        keltner_period: Keltner Channel period (default: 20)
        keltner_multiplier: Keltner Channel ATR multiplier (default: 1.5)
    """
    
    def __init__(self, bb_period=20, bb_std=2.0, keltner_period=20, keltner_multiplier=1.5, enable_short=True):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.keltner_period = keltner_period
        self.keltner_multiplier = keltner_multiplier
        self.enable_short = enable_short
        self.position = None
        self.squeeze_active = False
    
    def calculate_bollinger_bands(self, closes):
        """Calculate Bollinger Bands"""
        if len(closes) < self.bb_period:
            return None, None, None
        
        recent_closes = closes[-self.bb_period:]
        middle = np.mean(recent_closes)
        std_dev = np.std(recent_closes)
        
        upper_bb = middle + (self.bb_std * std_dev)
        lower_bb = middle - (self.bb_std * std_dev)
        
        return upper_bb, middle, lower_bb
    
    def calculate_keltner_channels(self, highs, lows, closes):
        """Calculate Keltner Channels"""
        if len(closes) < self.keltner_period + 1:
            return None, None, None
        
        # Calculate EMA for middle line (simplified as SMA)
        middle = np.mean(closes[-self.keltner_period:])
        
        # Calculate ATR
        true_ranges = []
        for i in range(1, len(closes)):
            if i >= len(closes) - self.keltner_period:
                high_low = highs[i] - lows[i]
                high_prev_close = abs(highs[i] - closes[i-1])
                low_prev_close = abs(lows[i] - closes[i-1])
                tr = max(high_low, high_prev_close, low_prev_close)
                true_ranges.append(tr)
        
        if len(true_ranges) < self.keltner_period:
            return None, None, None
        
        atr = np.mean(true_ranges)
        
        upper_kc = middle + (self.keltner_multiplier * atr)
        lower_kc = middle - (self.keltner_multiplier * atr)
        
        return upper_kc, middle, lower_kc
    
    def is_squeeze_active(self, bb_upper, bb_lower, kc_upper, kc_lower):
        """Check if squeeze is active (BB inside KC)"""
        if None in [bb_upper, bb_lower, kc_upper, kc_lower]:
            return False
        
        return bb_upper < kc_upper and bb_lower > kc_lower
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Bollinger Band squeeze"""
        if len(historical_data) < max(self.bb_period, self.keltner_period) + 1:
            return 'HOLD'
        
        closes = historical_data['close'].values
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        
        current_close = current_bar['close']
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        # Calculate Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(closes)
        
        # Calculate Keltner Channels
        kc_upper, kc_middle, kc_lower = self.calculate_keltner_channels(highs, lows, closes)
        
        if None in [bb_upper, bb_lower, kc_upper, kc_lower]:
            return 'HOLD'
        
        # Check squeeze status
        current_squeeze = self.is_squeeze_active(bb_upper, bb_lower, kc_upper, kc_lower)
        
        # Detect squeeze release (was in squeeze, now not)
        squeeze_release = self.squeeze_active and not current_squeeze
        self.squeeze_active = current_squeeze
        
        # Generate signals on squeeze release
        if squeeze_release:
            # Determine breakout direction
            if current_close > bb_middle:
                # Upward breakout
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    return 'BUY_LONG'
            else:
                # Downward breakout
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    return 'SELL_SHORT'
        
        # Exit signals
        elif self.position == 'LONG':
            # Exit if price falls back into the middle area
            if current_close < bb_middle:
                self.position = None
                return 'SELL_LONG'
        
        elif self.position == 'SHORT':
            # Exit if price rises back into the middle area
            if current_close > bb_middle:
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'