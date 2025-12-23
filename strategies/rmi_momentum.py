"""
Relative Momentum Index (RMI) Strategy

This strategy uses RMI which is similar to RSI but uses momentum
instead of simple price changes, making it more responsive.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Relative Momentum Index Strategy
    
    Parameters:
        rmi_period: RMI calculation period (default: 14)
        momentum_period: Momentum lookback period (default: 3)
        overbought_level: Overbought threshold (default: 70)
        oversold_level: Oversold threshold (default: 30)
    """
    
    def __init__(self, rmi_period=14, momentum_period=3, overbought_level=70, oversold_level=30, enable_short=True):
        self.rmi_period = rmi_period
        self.momentum_period = momentum_period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.enable_short = enable_short
        self.position = None
    
    def calculate_momentum(self, prices):
        """Calculate momentum (price change over momentum_period)"""
        momentum_values = []
        for i in range(self.momentum_period, len(prices)):
            momentum = prices[i] - prices[i - self.momentum_period]
            momentum_values.append(momentum)
        return momentum_values
    
    def calculate_rmi(self, closes):
        """Calculate Relative Momentum Index"""
        if len(closes) < self.rmi_period + self.momentum_period:
            return None
        
        # Calculate momentum
        momentum_values = self.calculate_momentum(closes)
        
        if len(momentum_values) < self.rmi_period:
            return None
        
        # Separate positive and negative momentum
        positive_momentum = [max(0, m) for m in momentum_values]
        negative_momentum = [abs(min(0, m)) for m in momentum_values]
        
        # Calculate smoothed averages (simplified Wilder's smoothing)
        recent_positive = positive_momentum[-self.rmi_period:]
        recent_negative = negative_momentum[-self.rmi_period:]
        
        avg_positive = np.mean(recent_positive)
        avg_negative = np.mean(recent_negative)
        
        # Calculate RMI
        if avg_negative == 0:
            return 100
        
        rs = avg_positive / avg_negative
        rmi = 100 - (100 / (1 + rs))
        
        return rmi
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on RMI levels"""
        if len(historical_data) < self.rmi_period + self.momentum_period + 1:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_closes = np.append(closes, current_bar['close'])
        
        rmi = self.calculate_rmi(current_closes)
        
        if rmi is None:
            return 'HOLD'
        
        # Generate signals
        
        # Buy: RMI oversold (strong selling momentum ending)
        if rmi <= self.oversold_level:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: RMI overbought (strong buying momentum ending)
        elif rmi >= self.overbought_level:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'