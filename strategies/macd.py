"""
MACD (Moving Average Convergence Divergence) Strategy with Long & Short

This strategy uses the MACD indicator crossover signals.
- Long: MACD line crosses above signal line
- Short: MACD line crosses below signal line
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    MACD Strategy with Long and Short trading
    
    Parameters:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
        enable_short: Enable short trading (default: True)
    """
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9, enable_short=True):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.enable_short = enable_short
        self.position = None
        self.prev_macd = None
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
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on MACD crossover"""
        if len(historical_data) < self.slow_period + self.signal_period:
            return 'HOLD'
        
        close_prices = historical_data['close'].values
        
        # Calculate MACD components
        fast_ema = self.calculate_ema(close_prices, self.fast_period)
        slow_ema = self.calculate_ema(close_prices, self.slow_period)
        
        if fast_ema is None or slow_ema is None:
            return 'HOLD'
        
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line (EMA of MACD line)
        # For simplicity, we'll approximate using recent MACD values
        if len(historical_data) < self.slow_period + self.signal_period + 10:
            return 'HOLD'
        
        # Simple approximation of signal line
        recent_data_len = min(self.signal_period * 2, len(historical_data))
        macd_values = []
        
        for i in range(recent_data_len):
            temp_data = close_prices[-(recent_data_len-i):]
            if len(temp_data) >= self.slow_period:
                temp_fast = self.calculate_ema(temp_data, self.fast_period)
                temp_slow = self.calculate_ema(temp_data, self.slow_period)
                if temp_fast is not None and temp_slow is not None:
                    macd_values.append(temp_fast - temp_slow)
        
        if len(macd_values) < self.signal_period:
            return 'HOLD'
        
        signal_line = self.calculate_ema(macd_values, self.signal_period)
        
        if signal_line is None:
            return 'HOLD'
        
        # Check for crossover
        trade_signal = 'HOLD'
        if self.prev_macd is not None and self.prev_signal is not None:
            # Bullish crossover: MACD crosses above signal
            if self.prev_macd <= self.prev_signal and macd_line > signal_line:
                if self.position == 'SHORT':
                    self.position = None
                    trade_signal = 'BUY_SHORT'
                elif self.position != 'LONG':
                    self.position = 'LONG'
                    trade_signal = 'BUY_LONG'
            
            # Bearish crossover: MACD crosses below signal
            elif self.prev_macd >= self.prev_signal and macd_line < signal_line:
                if self.position == 'LONG':
                    self.position = None
                    trade_signal = 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    self.position = 'SHORT'
                    trade_signal = 'SELL_SHORT'
        
        self.prev_macd = macd_line
        self.prev_signal = signal_line
        return trade_signal