"""
Chande Momentum Oscillator (CMO) Strategy

This strategy uses CMO which measures momentum using the sum of recent
gains and losses over a specified period.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Chande Momentum Oscillator Strategy
    
    Parameters:
        cmo_period: CMO calculation period (default: 14)
        overbought_level: Overbought threshold (default: 50)
        oversold_level: Oversold threshold (default: -50)
    """
    
    def __init__(self, cmo_period=14, overbought_level=50, oversold_level=-50, enable_short=True):
        self.cmo_period = cmo_period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.enable_short = enable_short
        self.position = None
    
    def calculate_cmo(self, closes):
        """Calculate Chande Momentum Oscillator"""
        if len(closes) < self.cmo_period + 1:
            return None
        
        # Calculate price changes
        changes = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            changes.append(change)
        
        if len(changes) < self.cmo_period:
            return None
        
        # Get recent changes
        recent_changes = changes[-self.cmo_period:]
        
        # Sum of positive and negative changes
        sum_positive = sum(change for change in recent_changes if change > 0)
        sum_negative = abs(sum(change for change in recent_changes if change < 0))
        
        # Calculate CMO
        if sum_positive + sum_negative == 0:
            return 0
        
        cmo = ((sum_positive - sum_negative) / (sum_positive + sum_negative)) * 100
        
        return cmo
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on CMO levels"""
        if len(historical_data) < self.cmo_period + 1:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_closes = np.append(closes, current_bar['close'])
        
        cmo = self.calculate_cmo(current_closes)
        
        if cmo is None:
            return 'HOLD'
        
        # Generate signals
        
        # Buy: CMO oversold (momentum turning from negative to positive)
        if cmo <= self.oversold_level:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: CMO overbought (momentum turning from positive to negative)
        elif cmo >= self.overbought_level:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'