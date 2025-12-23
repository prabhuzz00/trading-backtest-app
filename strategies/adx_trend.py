"""
ADX (Average Directional Index) Trend Strategy

This strategy uses ADX to measure trend strength along with +DI and -DI
to determine trend direction. Strong trends (ADX > 25) with directional 
movement provide trading signals.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    ADX Trend Strategy
    
    Parameters:
        period: ADX calculation period (default: 14)
        adx_threshold: Minimum ADX for strong trend (default: 25)
    """
    
    def __init__(self, period=14, adx_threshold=25, enable_short=True):
        self.period = period
        self.adx_threshold = adx_threshold
        self.enable_short = enable_short
        self.position = None
    
    def calculate_adx(self, highs, lows, closes):
        """Calculate ADX, +DI, and -DI"""
        if len(closes) < self.period + 1:
            return None, None, None
        
        # Calculate True Range (TR)
        tr_list = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_prev_close = abs(highs[i] - closes[i-1])
            low_prev_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_prev_close, low_prev_close)
            tr_list.append(tr)
        
        # Calculate Directional Movements
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(highs)):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            
            if high_diff > low_diff and high_diff > 0:
                plus_dm.append(high_diff)
                minus_dm.append(0)
            elif low_diff > high_diff and low_diff > 0:
                plus_dm.append(0)
                minus_dm.append(low_diff)
            else:
                plus_dm.append(0)
                minus_dm.append(0)
        
        # Smooth the values using simple moving average
        if len(tr_list) < self.period:
            return None, None, None
        
        atr = np.mean(tr_list[-self.period:])
        plus_di_raw = np.mean(plus_dm[-self.period:])
        minus_di_raw = np.mean(minus_dm[-self.period:])
        
        # Calculate DI+ and DI-
        plus_di = (plus_di_raw / atr) * 100 if atr != 0 else 0
        minus_di = (minus_di_raw / atr) * 100 if atr != 0 else 0
        
        # Calculate DX
        if plus_di + minus_di == 0:
            dx = 0
        else:
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        
        # ADX is the smoothed DX (simplified as current DX for this implementation)
        adx = dx
        
        return adx, plus_di, minus_di
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on ADX trend strength"""
        if len(historical_data) < self.period + 2:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        adx, plus_di, minus_di = self.calculate_adx(highs, lows, closes)
        
        if adx is None:
            return 'HOLD'
        
        # Only trade when trend is strong (ADX > threshold)
        if adx < self.adx_threshold:
            return 'HOLD'
        
        # Buy signal: Strong uptrend (+DI > -DI)
        if plus_di > minus_di:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell signal: Strong downtrend (-DI > +DI)
        elif minus_di > plus_di:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'