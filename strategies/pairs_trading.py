"""
Pairs Trading Strategy

This strategy trades the spread between two correlated assets. When the spread
deviates from its historical mean, it assumes mean reversion will occur.
For simplicity, this uses a ratio-based approach on a single asset against its moving average.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Pairs Trading Strategy (Simplified)
    
    Parameters:
        lookback_period: Period for calculating spread statistics (default: 60)
        entry_zscore: Z-score threshold for entry (default: 2.0)
        exit_zscore: Z-score threshold for exit (default: 0.5)
    """
    
    def __init__(self, lookback_period=60, entry_zscore=2.0, exit_zscore=0.5):
        self.lookback_period = lookback_period
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.position = None
        self.spread_history = []
    
    def calculate_spread_zscore(self, current_price, benchmark_price):
        """Calculate z-score of the price ratio spread"""
        # Use price ratio as spread
        current_spread = current_price / benchmark_price
        self.spread_history.append(current_spread)
        
        # Keep only lookback_period of history
        if len(self.spread_history) > self.lookback_period:
            self.spread_history = self.spread_history[-self.lookback_period:]
        
        if len(self.spread_history) < 20:  # Need minimum history
            return 0
        
        mean_spread = np.mean(self.spread_history)
        std_spread = np.std(self.spread_history)
        
        if std_spread == 0:
            return 0
        
        zscore = (current_spread - mean_spread) / std_spread
        return zscore
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on spread mean reversion"""
        if len(historical_data) < 50:  # Need sufficient history
            return 'HOLD'
        
        current_price = current_bar['close']
        
        # Use 20-period moving average as benchmark
        benchmark_price = np.mean(historical_data['close'].values[-20:])
        
        zscore = self.calculate_spread_zscore(current_price, benchmark_price)
        
        # Entry signals
        if abs(zscore) >= self.entry_zscore:
            if zscore > 0:  # Price too high relative to benchmark
                if self.position != 'SHORT':
                    self.position = 'SHORT'
                    return 'SELL'
            else:  # Price too low relative to benchmark
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
        
        # Exit signals
        elif abs(zscore) <= self.exit_zscore:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
            elif self.position == 'SHORT':
                self.position = None
                return 'BUY'
        
        return 'HOLD'