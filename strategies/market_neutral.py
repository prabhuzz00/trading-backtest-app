"""
Market Neutral Strategy

This strategy attempts to profit from relative price movements while
maintaining market neutrality by balancing long and short positions.
Simplified version using price vs. benchmark comparison.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Market Neutral Strategy (Simplified)
    
    Parameters:
        benchmark_period: Period for benchmark calculation (default: 50)
        alpha_threshold: Minimum alpha for position (default: 1.0%)
        rebalance_threshold: Threshold for rebalancing (default: 2.0%)
        max_position_size: Maximum position size (default: 1.0)
    """
    
    def __init__(self, benchmark_period=50, alpha_threshold=1.0, 
                 rebalance_threshold=2.0, max_position_size=1.0):
        self.benchmark_period = benchmark_period
        self.alpha_threshold = alpha_threshold
        self.rebalance_threshold = rebalance_threshold
        self.max_position_size = max_position_size
        self.position = None
        self.benchmark_history = []
        self.relative_performance = []
    
    def calculate_benchmark_return(self, closes):
        """Calculate benchmark return (market average approximation)"""
        if len(closes) < self.benchmark_period:
            return None
        
        # Use moving average as benchmark proxy
        benchmark_start = np.mean(closes[-self.benchmark_period:-self.benchmark_period//2])
        benchmark_end = np.mean(closes[-self.benchmark_period//2:])
        
        if benchmark_start == 0:
            return 0
        
        benchmark_return = (benchmark_end - benchmark_start) / benchmark_start
        return benchmark_return
    
    def calculate_stock_return(self, closes):
        """Calculate stock return over same period"""
        if len(closes) < self.benchmark_period:
            return None
        
        stock_start = closes[-self.benchmark_period//2]
        stock_end = closes[-1]
        
        if stock_start == 0:
            return 0
        
        stock_return = (stock_end - stock_start) / stock_start
        return stock_return
    
    def calculate_alpha(self, stock_return, benchmark_return):
        """Calculate alpha (excess return vs benchmark)"""
        if stock_return is None or benchmark_return is None:
            return 0
        
        alpha = stock_return - benchmark_return
        return alpha * 100  # Convert to percentage
    
    def calculate_beta(self):
        """Calculate beta (sensitivity to benchmark)"""
        if len(self.relative_performance) < 20:
            return 1.0  # Default beta
        
        # Simplified beta calculation using relative performance history
        recent_performance = self.relative_performance[-20:]
        
        # Calculate variance of relative performance
        variance = np.var(recent_performance)
        
        # Estimate beta based on variance (higher variance = higher beta)
        estimated_beta = max(0.5, min(2.0, 1.0 + variance * 10))
        
        return estimated_beta
    
    def calculate_position_size(self, alpha, beta):
        """Calculate optimal position size based on alpha and beta"""
        if abs(alpha) < self.alpha_threshold:
            return 0
        
        # Higher alpha = larger position
        # Lower beta = larger position (less market risk)
        alpha_factor = min(abs(alpha) / self.alpha_threshold, 3.0)  # Cap at 3x
        beta_factor = 2.0 / (1.0 + beta)  # Inverse relationship with beta
        
        position_size = alpha_factor * beta_factor * self.max_position_size
        
        # Apply sign based on alpha direction
        if alpha < 0:
            position_size = -position_size
        
        return max(-self.max_position_size, min(self.max_position_size, position_size))
    
    def generate_signal(self, current_bar, historical_data):
        """Generate market neutral signals"""
        if len(historical_data) < self.benchmark_period:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        
        # Calculate returns
        stock_return = self.calculate_stock_return(closes)
        benchmark_return = self.calculate_benchmark_return(closes)
        
        if stock_return is None or benchmark_return is None:
            return 'HOLD'
        
        # Calculate alpha and beta
        alpha = self.calculate_alpha(stock_return, benchmark_return)
        beta = self.calculate_beta()
        
        # Update performance history
        relative_perf = stock_return - benchmark_return
        self.relative_performance.append(relative_perf)
        if len(self.relative_performance) > 100:
            self.relative_performance = self.relative_performance[-100:]
        
        # Calculate target position size
        target_position = self.calculate_position_size(alpha, beta)
        
        # Determine current position state
        current_position_size = 0
        if self.position == 'LONG':
            current_position_size = 1.0
        elif self.position == 'SHORT':
            current_position_size = -1.0
        
        # Check if rebalancing is needed
        position_change = abs(target_position - current_position_size)
        
        if position_change >= self.rebalance_threshold / 100:
            # Significant alpha detected
            if target_position > 0.5:
                # Strong positive alpha - go long
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
            
            elif target_position < -0.5:
                # Strong negative alpha - exit long (or go short in full implementation)
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
            
            else:
                # Neutral alpha - close positions
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        return 'HOLD'