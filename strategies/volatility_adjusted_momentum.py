"""
Volatility-Adjusted Momentum Strategy

This strategy adjusts momentum signals based on current volatility levels,
taking larger positions in low volatility and smaller in high volatility.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Volatility-Adjusted Momentum Strategy
    
    Parameters:
        momentum_period: Period for momentum calculation (default: 10)
        volatility_period: Period for volatility calculation (default: 20)
        momentum_threshold: Base momentum threshold (default: 2.0)
    """
    
    def __init__(self, momentum_period=10, volatility_period=20, momentum_threshold=2.0, enable_short=True):
        self.momentum_period = momentum_period
        self.volatility_period = volatility_period
        self.momentum_threshold = momentum_threshold
        self.enable_short = enable_short
        self.position = None
        self.volatility_history = []
    
    def calculate_momentum(self, closes):
        """Calculate price momentum"""
        if len(closes) < self.momentum_period + 1:
            return None
        
        current_price = closes[-1]
        past_price = closes[-self.momentum_period - 1]
        
        if past_price == 0:
            return 0
        
        momentum = (current_price - past_price) / past_price * 100
        return momentum
    
    def calculate_volatility(self, closes):
        """Calculate realized volatility"""
        if len(closes) < self.volatility_period + 1:
            return None
        
        # Calculate returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                ret = np.log(closes[i] / closes[i-1])
                returns.append(ret)
        
        if len(returns) < self.volatility_period:
            return None
        
        recent_returns = returns[-self.volatility_period:]
        volatility = np.std(recent_returns)
        
        return volatility
    
    def adjust_threshold_for_volatility(self, base_threshold, current_vol):
        """Adjust momentum threshold based on volatility"""
        if len(self.volatility_history) < 50:
            return base_threshold
        
        # Calculate volatility percentile
        vol_array = np.array(self.volatility_history)
        vol_percentile = np.percentile(vol_array, 50)  # Median
        
        if vol_percentile == 0:
            return base_threshold
        
        # Adjust threshold: higher threshold in high vol, lower in low vol
        vol_ratio = current_vol / vol_percentile
        adjusted_threshold = base_threshold * vol_ratio
        
        # Clamp to reasonable range
        adjusted_threshold = max(0.5, min(5.0, adjusted_threshold))
        
        return adjusted_threshold
    
    def generate_signal(self, current_bar, historical_data):
        """Generate volatility-adjusted momentum signals"""
        if len(historical_data) < max(self.momentum_period + 1, self.volatility_period + 1):
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        
        # Calculate momentum and volatility
        momentum = self.calculate_momentum(closes)
        volatility = self.calculate_volatility(closes)
        
        if momentum is None or volatility is None:
            return 'HOLD'
        
        # Update volatility history
        self.volatility_history.append(volatility)
        if len(self.volatility_history) > 100:
            self.volatility_history = self.volatility_history[-100:]
        
        # Adjust momentum threshold for current volatility
        adjusted_threshold = self.adjust_threshold_for_volatility(
            self.momentum_threshold, volatility)
        
        # Generate signals
        
        # Buy: Positive momentum above adjusted threshold
        if momentum >= adjusted_threshold:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: Negative momentum below negative adjusted threshold
        elif momentum <= -adjusted_threshold:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit on momentum fade (momentum between -threshold/2 and threshold/2)
        elif abs(momentum) <= adjusted_threshold / 2:
            if self.position == 'LONG':
                self.position = None
                return 'SELL_LONG'
            elif self.position == 'SHORT':
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'