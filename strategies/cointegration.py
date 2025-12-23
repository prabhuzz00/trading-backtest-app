"""
Cointegration Strategy

This strategy identifies cointegrated relationships between price series
and trades when they deviate from their long-term equilibrium relationship.
Note: This simplified version uses a single asset against its trend.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Cointegration Strategy (Simplified)
    
    Parameters:
        lookback_period: Period for cointegration analysis (default: 100)
        entry_threshold: Z-score threshold for entry (default: 2.0)
        exit_threshold: Z-score threshold for exit (default: 0.5)
        half_life_period: Expected mean reversion period (default: 20)
    """
    
    def __init__(self, lookback_period=100, entry_threshold=2.0, 
                 exit_threshold=0.5, half_life_period=20):
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.half_life_period = half_life_period
        self.position = None
        self.spread_history = []
    
    def calculate_long_term_relationship(self, prices):
        """Calculate long-term trend relationship"""
        if len(prices) < self.lookback_period:
            return None, None
        
        # Use linear trend as the "cointegrating" relationship
        x = np.arange(len(prices))
        slope, intercept = np.polyfit(x, prices, 1)
        
        return slope, intercept
    
    def calculate_spread(self, prices, slope, intercept):
        """Calculate spread from long-term relationship"""
        if slope is None or intercept is None:
            return None
        
        x = len(prices) - 1
        expected_price = slope * x + intercept
        current_price = prices[-1]
        
        spread = current_price - expected_price
        return spread
    
    def calculate_spread_zscore(self):
        """Calculate z-score of current spread"""
        if len(self.spread_history) < 20:
            return 0
        
        mean_spread = np.mean(self.spread_history)
        std_spread = np.std(self.spread_history)
        
        if std_spread == 0:
            return 0
        
        current_spread = self.spread_history[-1]
        zscore = (current_spread - mean_spread) / std_spread
        
        return zscore
    
    def estimate_half_life(self):
        """Estimate half-life of mean reversion"""
        if len(self.spread_history) < 30:
            return self.half_life_period
        
        # Simple AR(1) estimation for half-life
        spreads = np.array(self.spread_history[-30:])
        lagged_spreads = spreads[:-1]
        current_spreads = spreads[1:]
        
        if len(lagged_spreads) == 0:
            return self.half_life_period
        
        # Linear regression: spread[t] = alpha + beta * spread[t-1] + error
        try:
            correlation_matrix = np.corrcoef(lagged_spreads, current_spreads)
            if correlation_matrix.shape == (2, 2):
                beta = correlation_matrix[0, 1] * (np.std(current_spreads) / np.std(lagged_spreads))
            else:
                beta = 0.95  # Default value
        except:
            beta = 0.95
        
        if beta >= 1:
            return self.half_life_period
        
        half_life = -np.log(2) / np.log(beta)
        return max(5, min(50, half_life))  # Clamp to reasonable range
    
    def generate_signal(self, current_bar, historical_data):
        """Generate cointegration-based trading signals"""
        if len(historical_data) < self.lookback_period:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        
        # Calculate long-term relationship
        slope, intercept = self.calculate_long_term_relationship(closes)
        
        if slope is None:
            return 'HOLD'
        
        # Calculate current spread
        all_prices = np.append(closes, current_close)
        current_spread = self.calculate_spread(all_prices, slope, intercept)
        
        if current_spread is None:
            return 'HOLD'
        
        # Update spread history
        self.spread_history.append(current_spread)
        if len(self.spread_history) > self.lookback_period:
            self.spread_history = self.spread_history[-self.lookback_period:]
        
        # Calculate z-score
        zscore = self.calculate_spread_zscore()
        
        # Estimate current half-life
        half_life = self.estimate_half_life()
        
        # Adjust thresholds based on half-life (faster mean reversion = lower thresholds)
        adjusted_entry = self.entry_threshold * (half_life / self.half_life_period) ** 0.5
        adjusted_exit = self.exit_threshold * (half_life / self.half_life_period) ** 0.5
        
        # Generate signals
        
        # Entry signals
        if abs(zscore) >= adjusted_entry:
            if zscore < 0:  # Price below long-term relationship
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
            else:  # Price above long-term relationship
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        # Exit signals
        elif abs(zscore) <= adjusted_exit:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        return 'HOLD'