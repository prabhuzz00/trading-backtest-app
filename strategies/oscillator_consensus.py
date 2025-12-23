"""
Oversold/Overbought Oscillator Strategy

This strategy combines multiple oscillators (RSI, Stochastic, Williams %R)
to identify extreme overbought/oversold conditions for mean reversion trades.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Oversold/Overbought Oscillator Strategy
    
    Parameters:
        rsi_period: RSI period (default: 14)
        stoch_period: Stochastic period (default: 14)
        williams_period: Williams %R period (default: 14)
        oversold_threshold: Oversold threshold (default: 30)
        overbought_threshold: Overbought threshold (default: 70)
    """
    
    def __init__(self, rsi_period=14, stoch_period=14, williams_period=14, 
                 oversold_threshold=30, overbought_threshold=70):
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.williams_period = williams_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.position = None
    
    def calculate_rsi(self, prices):
        """Calculate RSI"""
        if len(prices) < self.rsi_period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:self.rsi_period])
        avg_loss = np.mean(losses[:self.rsi_period])
        
        for i in range(self.rsi_period, len(deltas)):
            avg_gain = ((avg_gain * (self.rsi_period - 1)) + gains[i]) / self.rsi_period
            avg_loss = ((avg_loss * (self.rsi_period - 1)) + losses[i]) / self.rsi_period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_stochastic_k(self, highs, lows, closes):
        """Calculate Stochastic %K"""
        if len(closes) < self.stoch_period:
            return None
        
        lowest_low = np.min(lows[-self.stoch_period:])
        highest_high = np.max(highs[-self.stoch_period:])
        current_close = closes[-1]
        
        if highest_high == lowest_low:
            return 50
        
        k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        return k_percent
    
    def calculate_williams_r(self, highs, lows, closes):
        """Calculate Williams %R"""
        if len(closes) < self.williams_period:
            return None
        
        highest_high = np.max(highs[-self.williams_period:])
        lowest_low = np.min(lows[-self.williams_period:])
        current_close = closes[-1]
        
        if highest_high == lowest_low:
            return -50
        
        williams_r = ((highest_high - current_close) / (highest_high - lowest_low)) * -100
        return williams_r
    
    def generate_signal(self, current_bar, historical_data):
        """Generate signal based on multiple oscillator consensus"""
        min_periods = max(self.rsi_period, self.stoch_period, self.williams_period) + 1
        if len(historical_data) < min_periods:
            return 'HOLD'
        
        closes = historical_data['close'].values
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        
        # Calculate oscillators
        rsi = self.calculate_rsi(closes)
        stoch_k = self.calculate_stochastic_k(highs, lows, closes)
        williams_r = self.calculate_williams_r(highs, lows, closes)
        
        if None in [rsi, stoch_k, williams_r]:
            return 'HOLD'
        
        # Convert Williams %R to 0-100 scale for consistency
        williams_normalized = williams_r + 100
        
        # Count oscillators in oversold/overbought territory
        oscillators = [rsi, stoch_k, williams_normalized]
        
        oversold_count = sum(1 for osc in oscillators if osc <= self.oversold_threshold)
        overbought_count = sum(1 for osc in oscillators if osc >= self.overbought_threshold)
        
        # Require consensus (at least 2 out of 3 oscillators)
        
        # Buy signal: Multiple oscillators oversold
        if oversold_count >= 2:
            if self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY'
        
        # Sell signal: Multiple oscillators overbought
        elif overbought_count >= 2:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        # Exit when oscillators return to neutral
        elif self.position == 'LONG' and oversold_count == 0:
            neutral_count = sum(1 for osc in oscillators 
                              if self.oversold_threshold < osc < self.overbought_threshold)
            if neutral_count >= 2:
                self.position = None
                return 'SELL'
        
        return 'HOLD'