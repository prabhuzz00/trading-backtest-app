"""
Statistical Arbitrage Strategy

This strategy identifies statistical relationships and exploits temporary
price divergences. Uses z-score analysis of price deviations from 
expected values based on historical patterns.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Statistical Arbitrage Strategy
    
    Parameters:
        lookback_window: Window for statistical analysis (default: 100)
        entry_threshold: Z-score threshold for entry (default: 2.5)
        exit_threshold: Z-score threshold for exit (default: 0.5)
    """
    
    def __init__(self, lookback_window=100, entry_threshold=2.5, exit_threshold=0.5):
        self.lookback_window = lookback_window
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.position = None
        self.price_residuals = []
    
    def calculate_expected_price(self, historical_data):
        """Calculate expected price based on statistical model"""
        if len(historical_data) < 20:
            return None
        
        closes = historical_data['close'].values
        
        # Simple linear trend model using numpy polyfit
        x = np.arange(len(closes))
        slope, intercept = np.polyfit(x, closes, 1)
        
        # Expected price for next period
        expected_price = slope * len(closes) + intercept
        
        return expected_price
    
    def calculate_price_zscore(self, current_price, expected_price, historical_residuals):
        """Calculate z-score of price deviation"""
        if expected_price is None or len(historical_residuals) < 10:
            return 0
        
        residual = current_price - expected_price
        
        mean_residual = np.mean(historical_residuals)
        std_residual = np.std(historical_residuals)
        
        if std_residual == 0:
            return 0
        
        zscore = (residual - mean_residual) / std_residual
        return zscore
    
    def generate_signal(self, current_bar, historical_data):
        """Generate statistical arbitrage signals"""
        if len(historical_data) < 30:
            return 'HOLD'
        
        current_price = current_bar['close']
        
        # Calculate expected price
        expected_price = self.calculate_expected_price(historical_data)
        
        if expected_price is None:
            return 'HOLD'
        
        # Update residuals history
        residual = current_price - expected_price
        self.price_residuals.append(residual)
        
        if len(self.price_residuals) > self.lookback_window:
            self.price_residuals = self.price_residuals[-self.lookback_window:]
        
        # Calculate z-score
        zscore = self.calculate_price_zscore(current_price, expected_price, self.price_residuals)
        
        # Trading logic
        if abs(zscore) >= self.entry_threshold:
            if zscore < 0:  # Price below expected (undervalued)
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
            else:  # Price above expected (overvalued)
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        # Exit when z-score returns to normal range
        elif abs(zscore) <= self.exit_threshold:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        return 'HOLD'