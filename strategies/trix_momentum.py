"""
TRIX Strategy

This strategy uses TRIX (Triple Exponential Average) indicator which
is a momentum oscillator that filters out market noise through triple smoothing.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    TRIX Momentum Strategy
    
    Parameters:
        trix_period: TRIX calculation period (default: 14)
        signal_period: Signal line EMA period (default: 9)
    """
    
    def __init__(self, trix_period=14, signal_period=9, enable_short=True):
        self.trix_period = trix_period
        self.signal_period = signal_period
        self.enable_short = enable_short
        self.position = None
        self.prev_trix = None
        self.prev_signal = None
    
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def calculate_trix(self, closes):
        """Calculate TRIX (Triple Exponential Average)"""
        if len(closes) < self.trix_period * 3:
            return None
        
        # First EMA
        ema1_values = []
        for i in range(len(closes)):
            if i >= self.trix_period - 1:
                ema1 = self.calculate_ema(closes[i - self.trix_period + 1:i + 1], self.trix_period)
                if ema1 is not None:
                    ema1_values.append(ema1)
        
        if len(ema1_values) < self.trix_period:
            return None
        
        # Second EMA (EMA of first EMA)
        ema2_values = []
        for i in range(len(ema1_values)):
            if i >= self.trix_period - 1:
                ema2 = self.calculate_ema(ema1_values[i - self.trix_period + 1:i + 1], self.trix_period)
                if ema2 is not None:
                    ema2_values.append(ema2)
        
        if len(ema2_values) < self.trix_period:
            return None
        
        # Third EMA (EMA of second EMA)
        ema3_values = []
        for i in range(len(ema2_values)):
            if i >= self.trix_period - 1:
                ema3 = self.calculate_ema(ema2_values[i - self.trix_period + 1:i + 1], self.trix_period)
                if ema3 is not None:
                    ema3_values.append(ema3)
        
        if len(ema3_values) < 2:
            return None
        
        # TRIX = (Current EMA3 - Previous EMA3) / Previous EMA3 * 10000
        current_ema3 = ema3_values[-1]
        prev_ema3 = ema3_values[-2]
        
        if prev_ema3 == 0:
            return 0
        
        trix = ((current_ema3 - prev_ema3) / prev_ema3) * 10000
        
        return trix
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on TRIX momentum"""
        if len(historical_data) < self.trix_period * 3 + self.signal_period:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_closes = np.append(closes, current_bar['close'])
        
        trix = self.calculate_trix(current_closes)
        
        if trix is None:
            return 'HOLD'
        
        # Simple zero-line cross strategy
        if self.prev_trix is not None:
            # Buy: TRIX crosses above zero (momentum turning positive)
            if self.prev_trix <= 0 and trix > 0:
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    self.prev_trix = trix
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    self.prev_trix = trix
                    return 'BUY_LONG'
            
            # Sell: TRIX crosses below zero (momentum turning negative)
            elif self.prev_trix >= 0 and trix < 0:
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    self.prev_trix = trix
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    self.prev_trix = trix
                    return 'SELL_SHORT'
        
        self.prev_trix = trix
        return 'HOLD'