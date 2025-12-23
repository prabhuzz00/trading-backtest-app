"""
Average True Range (ATR) Breakout Strategy

This strategy uses ATR to measure volatility and trades breakouts
when price moves beyond ATR-based bands.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    ATR Breakout Strategy
    
    Parameters:
        atr_period: ATR calculation period (default: 14)
        atr_multiplier: ATR multiplier for breakout bands (default: 2.0)
        ma_period: Moving average period for trend filter (default: 20)
    """
    
    def __init__(self, atr_period=14, atr_multiplier=2.0, ma_period=20, enable_short=True):
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.ma_period = ma_period
        self.enable_short = enable_short
        self.position = None
    
    def calculate_true_range(self, highs, lows, closes):
        """Calculate True Range values"""
        if len(closes) < 2:
            return []
        
        true_ranges = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_prev_close = abs(highs[i] - closes[i-1])
            low_prev_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_prev_close, low_prev_close)
            true_ranges.append(tr)
        
        return true_ranges
    
    def calculate_atr(self, highs, lows, closes):
        """Calculate Average True Range"""
        true_ranges = self.calculate_true_range(highs, lows, closes)
        
        if len(true_ranges) < self.atr_period:
            return None
        
        atr = np.mean(true_ranges[-self.atr_period:])
        return atr
    
    def calculate_moving_average(self, prices):
        """Calculate simple moving average"""
        if len(prices) < self.ma_period:
            return None
        
        return np.mean(prices[-self.ma_period:])
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on ATR breakout"""
        if len(historical_data) < max(self.atr_period + 1, self.ma_period):
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Calculate ATR
        atr = self.calculate_atr(highs, lows, closes)
        
        if atr is None:
            return 'HOLD'
        
        # Calculate moving average for trend filter
        ma_value = self.calculate_moving_average(closes)
        
        if ma_value is None:
            return 'HOLD'
        
        # Calculate breakout levels
        previous_close = closes[-1]
        upper_breakout = previous_close + (self.atr_multiplier * atr)
        lower_breakout = previous_close - (self.atr_multiplier * atr)
        
        # Generate signals
        
        # Buy: Price breaks above upper level and above MA (trending up)
        if current_high > upper_breakout and current_close > ma_value:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: Price breaks below lower level or falls below MA
        elif current_low < lower_breakout or current_close < ma_value:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short and current_close < ma_value:
                # Open short position when trending down
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'