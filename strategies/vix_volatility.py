"""
VIX-Based Volatility Strategy

This strategy trades based on volatility regimes. In low volatility periods,
it expects mean reversion. In high volatility periods, it follows momentum.
Note: This simplified version uses price volatility as a proxy for VIX.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    VIX-Based Volatility Strategy
    
    Parameters:
        volatility_period: Period for volatility calculation (default: 20)
        high_vol_threshold: High volatility threshold percentile (default: 80)
        low_vol_threshold: Low volatility threshold percentile (default: 20)
    """
    
    def __init__(self, volatility_period=20, high_vol_threshold=80, low_vol_threshold=20):
        self.volatility_period = volatility_period
        self.high_vol_threshold = high_vol_threshold
        self.low_vol_threshold = low_vol_threshold
        self.position = None
        self.volatility_history = []
    
    def calculate_realized_volatility(self, closes):
        """Calculate realized volatility"""
        if len(closes) < 2:
            return None
        
        # Calculate log returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                ret = np.log(closes[i] / closes[i-1])
                returns.append(ret)
        
        if len(returns) < self.volatility_period:
            return None
        
        # Calculate volatility
        recent_returns = returns[-self.volatility_period:]
        volatility = np.std(recent_returns) * np.sqrt(252)  # Annualized
        
        return volatility
    
    def get_volatility_regime(self):
        """Determine current volatility regime"""
        if len(self.volatility_history) < 100:  # Need sufficient history
            return 'NORMAL'
        
        # Calculate percentiles
        vol_array = np.array(self.volatility_history)
        high_threshold = np.percentile(vol_array, self.high_vol_threshold)
        low_threshold = np.percentile(vol_array, self.low_vol_threshold)
        
        current_vol = self.volatility_history[-1]
        
        if current_vol >= high_threshold:
            return 'HIGH'
        elif current_vol <= low_threshold:
            return 'LOW'
        else:
            return 'NORMAL'
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on volatility regime"""
        if len(historical_data) < self.volatility_period + 1:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        
        # Calculate current volatility
        volatility = self.calculate_realized_volatility(closes)
        
        if volatility is None:
            return 'HOLD'
        
        # Update volatility history
        self.volatility_history.append(volatility)
        if len(self.volatility_history) > 252:  # Keep 1 year of history
            self.volatility_history = self.volatility_history[-252:]
        
        # Get volatility regime
        regime = self.get_volatility_regime()
        
        if regime == 'NORMAL':
            return 'HOLD'
        
        # Calculate short-term momentum
        if len(closes) >= 5:
            momentum = (current_close - closes[-5]) / closes[-5] * 100
        else:
            momentum = 0
        
        # Calculate mean reversion signal
        if len(closes) >= 20:
            mean_price = np.mean(closes[-20:])
            std_price = np.std(closes[-20:])
            if std_price > 0:
                z_score = (current_close - mean_price) / std_price
            else:
                z_score = 0
        else:
            z_score = 0
        
        # Trading logic based on regime
        
        if regime == 'LOW':
            # Low volatility: Use mean reversion
            if z_score <= -1.5:  # Oversold
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
            elif z_score >= 1.0:  # Return to mean
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        elif regime == 'HIGH':
            # High volatility: Follow momentum
            if momentum >= 2.0:  # Strong positive momentum
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
            elif momentum <= -2.0:  # Strong negative momentum
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        return 'HOLD'