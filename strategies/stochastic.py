"""
Stochastic Oscillator Strategy with Long & Short

This strategy uses the Stochastic Oscillator with %K and %D crossovers.
- Long: Oversold area, %K crosses above %D
- Short: Overbought area, %K crosses below %D
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Stochastic Oscillator Strategy with Long and Short trading
    
    Parameters:
        k_period: %K period (default: 14)
        d_period: %D period (default: 3)
        oversold: Oversold threshold (default: 20)
        overbought: Overbought threshold (default: 80)
        enable_short: Enable short trading (default: True)
    """
    
    def __init__(self, k_period=14, d_period=3, oversold=20, overbought=80, enable_short=True):
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
        self.enable_short = enable_short
        self.position = None
    
    def calculate_stochastic(self, highs, lows, closes):
        """Calculate Stochastic %K and %D"""
        if len(closes) < self.k_period:
            return None, None
        
        # Calculate %K
        lowest_low = np.min(lows[-self.k_period:])
        highest_high = np.max(highs[-self.k_period:])
        current_close = closes[-1]
        
        if highest_high == lowest_low:
            k_percent = 50  # Avoid division by zero
        else:
            k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # For %D, we need multiple %K values
        if len(closes) < self.k_period + self.d_period - 1:
            return k_percent, None
        
        k_values = []
        for i in range(self.d_period):
            end_idx = len(closes) - i
            start_idx = end_idx - self.k_period
            
            if start_idx < 0:
                break
                
            period_lows = lows[start_idx:end_idx]
            period_highs = highs[start_idx:end_idx]
            period_close = closes[end_idx - 1]
            
            period_lowest = np.min(period_lows)
            period_highest = np.max(period_highs)
            
            if period_highest == period_lowest:
                k_val = 50
            else:
                k_val = ((period_close - period_lowest) / (period_highest - period_lowest)) * 100
            
            k_values.append(k_val)
        
        d_percent = np.mean(k_values) if k_values else None
        
        return k_percent, d_percent
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Stochastic Oscillator"""
        if len(historical_data) < self.k_period + self.d_period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        k_percent, d_percent = self.calculate_stochastic(highs, lows, closes)
        
        if k_percent is None or d_percent is None:
            return 'HOLD'
        
        # Long signal: Stochastic in oversold area and %K crosses above %D
        if k_percent <= self.oversold and d_percent <= self.oversold and k_percent > d_percent:
            if self.position == 'SHORT':
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Short signal: Stochastic in overbought area and %K crosses below %D
        elif k_percent >= self.overbought and d_percent >= self.overbought and k_percent < d_percent:
            if self.position == 'LONG':
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'