"""
Keltner Channel Mean Reversion Strategy

This strategy uses Keltner Channels which are volatility-based bands around
an EMA. It trades mean reversion when price touches the outer bands.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Keltner Channel Mean Reversion Strategy
    
    Parameters:
        ema_period: EMA period for middle line (default: 20)
        atr_period: ATR period for band width (default: 20)
        multiplier: ATR multiplier for band distance (default: 2.0)
    """
    
    def __init__(self, ema_period=20, atr_period=20, multiplier=2.0, enable_short=True):
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.enable_short = enable_short
        self.position = None
    
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def calculate_atr(self, highs, lows, closes, period):
        """Calculate Average True Range"""
        if len(closes) < period + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_prev_close = abs(highs[i] - closes[i-1])
            low_prev_close = abs(lows[i] - closes[i-1])
            true_range = max(high_low, high_prev_close, low_prev_close)
            true_ranges.append(true_range)
        
        if len(true_ranges) < period:
            return None
        
        atr = np.mean(true_ranges[-period:])
        return atr
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Keltner Channel mean reversion"""
        if len(historical_data) < max(self.ema_period, self.atr_period) + 1:
            return 'HOLD'
        
        closes = historical_data['close'].values
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        current_price = current_bar['close']
        
        # Calculate Keltner Channel components
        middle_line = self.calculate_ema(closes, self.ema_period)
        atr = self.calculate_atr(highs, lows, closes, self.atr_period)
        
        if middle_line is None or atr is None:
            return 'HOLD'
        
        upper_band = middle_line + (self.multiplier * atr)
        lower_band = middle_line - (self.multiplier * atr)
        
        # Mean reversion signals
        # Buy when price touches lower band
        if current_price <= lower_band:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell when price touches upper band
        elif current_price >= upper_band:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit when price returns to middle line
        elif self.position == 'LONG' and current_price >= middle_line:
            self.position = None
            return 'SELL_LONG'
        
        elif self.position == 'SHORT' and current_price <= middle_line:
            self.position = None
            return 'BUY_SHORT'
        
        return 'HOLD'