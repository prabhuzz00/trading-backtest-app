"""
Volatility Contraction Pattern Strategy

This strategy identifies periods of low volatility (contraction) and
expects a breakout when volatility expands.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Volatility Contraction Pattern Strategy
    
    Parameters:
        volatility_period: Period for volatility calculation (default: 20)
        contraction_threshold: Threshold for identifying contraction (default: 0.5)
        breakout_multiplier: Multiplier for breakout level (default: 1.5)
    """
    
    def __init__(self, volatility_period=20, contraction_threshold=0.5, breakout_multiplier=1.5, enable_short=True):
        self.volatility_period = volatility_period
        self.contraction_threshold = contraction_threshold
        self.breakout_multiplier = breakout_multiplier
        self.enable_short = enable_short
        self.position = None
        self.volatility_history = []
    
    def calculate_volatility(self, closes):
        """Calculate price volatility (standard deviation of returns)"""
        if len(closes) < 2:
            return None
        
        # Calculate returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] != 0:
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(ret)
        
        if len(returns) < self.volatility_period:
            return None
        
        # Calculate volatility as standard deviation of returns
        recent_returns = returns[-self.volatility_period:]
        volatility = np.std(recent_returns) * np.sqrt(252)  # Annualized
        
        return volatility
    
    def is_volatility_contracting(self):
        """Check if volatility is contracting (decreasing)"""
        if len(self.volatility_history) < 10:
            return False
        
        recent_vol = np.mean(self.volatility_history[-5:])
        older_vol = np.mean(self.volatility_history[-10:-5])
        
        # Volatility contraction: recent vol significantly lower than older vol
        if older_vol > 0:
            vol_ratio = recent_vol / older_vol
            return vol_ratio < self.contraction_threshold
        
        return False
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on volatility patterns"""
        if len(historical_data) < self.volatility_period + 10:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        # Calculate current volatility
        volatility = self.calculate_volatility(closes)
        
        if volatility is None:
            return 'HOLD'
        
        # Update volatility history
        self.volatility_history.append(volatility)
        if len(self.volatility_history) > 50:  # Keep limited history
            self.volatility_history = self.volatility_history[-50:]
        
        # Check for volatility contraction
        is_contracting = self.is_volatility_contracting()
        
        if not is_contracting:
            return 'HOLD'
        
        # Calculate breakout levels during contraction period
        recent_closes = closes[-10:]  # Recent price range
        recent_high = np.max(recent_closes)
        recent_low = np.min(recent_closes)
        range_size = recent_high - recent_low
        
        upper_breakout = recent_high + (self.breakout_multiplier * range_size * volatility)
        lower_breakout = recent_low - (self.breakout_multiplier * range_size * volatility)
        
        # Generate signals on volatility expansion breakouts
        
        # Buy: Upward breakout during volatility expansion
        if current_high > upper_breakout:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: Downward breakout
        elif current_low < lower_breakout:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'