"""
RSI (Relative Strength Index) Strategy with Long & Short Support

This strategy uses RSI to identify overbought and oversold conditions.
- Long: Buy when RSI crosses below oversold, Sell when crosses above overbought
- Short: Sell short when RSI crosses above overbought, Cover when crosses below oversold
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    RSI Strategy with Long and Short trading
    
    Parameters:
        period: RSI calculation period (default: 14)
        oversold: Oversold threshold (default: 30)
        overbought: Overbought threshold (default: 70)
        enable_short: Enable short trading (default: True)
    """
    
    def __init__(self, period=14, oversold=30, overbought=70, enable_short=True):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.enable_short = enable_short
        self.position = None  # 'LONG', 'SHORT', or None
        self.prev_rsi = None  # Track previous RSI for crossover detection
    
    def calculate_rsi(self, prices):
        """Calculate RSI"""
        if len(prices) < self.period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[:self.period])
        avg_loss = np.mean(losses[:self.period])
        
        # Calculate subsequent RSI values using smoothed averages
        for i in range(self.period, len(deltas)):
            avg_gain = ((avg_gain * (self.period - 1)) + gains[i]) / self.period
            avg_loss = ((avg_loss * (self.period - 1)) + losses[i]) / self.period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on RSI crossovers"""
        if len(historical_data) < self.period + 1:
            return 'HOLD'
        
        close_prices = historical_data['close'].values
        rsi = self.calculate_rsi(close_prices)
        
        if rsi is None:
            return 'HOLD'
        
        # Initialize prev_rsi on first call
        if self.prev_rsi is None:
            self.prev_rsi = rsi
            return 'HOLD'
        
        signal = 'HOLD'
        
        # Detect RSI crossing below oversold threshold
        if self.prev_rsi > self.oversold and rsi <= self.oversold:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                signal = 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                signal = 'BUY_LONG'
        
        # Detect RSI crossing above overbought threshold
        elif self.prev_rsi < self.overbought and rsi >= self.overbought:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                signal = 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                signal = 'SELL_SHORT'
        
        # Update previous RSI for next iteration
        self.prev_rsi = rsi
        
        return signal