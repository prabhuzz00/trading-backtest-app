"""
Long-Short Equity Strategy

This strategy takes long positions in outperforming stocks and short positions
in underperforming stocks based on relative strength analysis.
Simplified version using single asset vs. its own performance metrics.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Long-Short Equity Strategy (Simplified)
    
    Parameters:
        performance_period: Period for performance analysis (default: 30)
        ranking_period: Period for relative ranking (default: 60)
        entry_percentile: Percentile threshold for entries (default: 80)
        exit_percentile: Percentile threshold for exits (default: 60)
    """
    
    def __init__(self, performance_period=30, ranking_period=60, 
                 entry_percentile=80, exit_percentile=60):
        self.performance_period = performance_period
        self.ranking_period = ranking_period
        self.entry_percentile = entry_percentile
        self.exit_percentile = exit_percentile
        self.position = None
        self.performance_history = []
    
    def calculate_relative_performance(self, closes):
        """Calculate various performance metrics"""
        if len(closes) < self.performance_period:
            return None
        
        # Calculate different performance metrics
        metrics = {}
        
        # Short-term momentum
        if len(closes) >= 5:
            metrics['momentum_5d'] = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
        
        # Medium-term momentum
        if len(closes) >= self.performance_period:
            metrics['momentum_period'] = (closes[-1] - closes[-self.performance_period]) / closes[-self.performance_period] if closes[-self.performance_period] != 0 else 0
        
        # Volatility-adjusted return (Sharpe-like ratio)
        if len(closes) >= self.performance_period:
            returns = []
            for i in range(1, self.performance_period + 1):
                if closes[-i-1] != 0:
                    ret = (closes[-i] - closes[-i-1]) / closes[-i-1]
                    returns.append(ret)
            
            if returns:
                avg_return = np.mean(returns)
                vol = np.std(returns)
                metrics['risk_adjusted'] = avg_return / vol if vol != 0 else 0
            else:
                metrics['risk_adjusted'] = 0
        
        # Trend strength
        if len(closes) >= self.performance_period:
            x = np.arange(self.performance_period)
            recent_prices = closes[-self.performance_period:]
            correlation = np.corrcoef(x, recent_prices)[0, 1] if len(recent_prices) == len(x) else 0
            metrics['trend_strength'] = correlation
        
        # Relative strength vs moving average
        if len(closes) >= self.performance_period:
            ma = np.mean(closes[-self.performance_period:])
            metrics['relative_to_ma'] = (closes[-1] - ma) / ma if ma != 0 else 0
        
        return metrics
    
    def calculate_composite_score(self, metrics):
        """Calculate composite performance score"""
        if metrics is None:
            return 0
        
        # Weight different metrics
        weights = {
            'momentum_5d': 0.2,
            'momentum_period': 0.3,
            'risk_adjusted': 0.2,
            'trend_strength': 0.15,
            'relative_to_ma': 0.15
        }
        
        composite_score = 0
        total_weight = 0
        
        for metric, value in metrics.items():
            if metric in weights:
                composite_score += value * weights[metric]
                total_weight += weights[metric]
        
        if total_weight > 0:
            composite_score /= total_weight
        
        return composite_score
    
    def calculate_percentile_rank(self, current_score):
        """Calculate percentile rank of current performance"""
        if len(self.performance_history) < 20:
            return 50  # Neutral if insufficient history
        
        # Count how many historical scores are below current score
        below_count = sum(1 for score in self.performance_history if score < current_score)
        percentile = (below_count / len(self.performance_history)) * 100
        
        return percentile
    
    def generate_signal(self, current_bar, historical_data):
        """Generate long-short equity signals"""
        if len(historical_data) < self.ranking_period:
            return 'HOLD'
        
        closes = historical_data['close'].values
        
        # Calculate current performance metrics
        current_metrics = self.calculate_relative_performance(closes)
        
        if current_metrics is None:
            return 'HOLD'
        
        # Calculate composite score
        current_score = self.calculate_composite_score(current_metrics)
        
        # Update performance history
        self.performance_history.append(current_score)
        if len(self.performance_history) > self.ranking_period:
            self.performance_history = self.performance_history[-self.ranking_period:]
        
        # Calculate percentile rank
        percentile_rank = self.calculate_percentile_rank(current_score)
        
        # Generate trading signals based on percentile ranking
        
        # Enter long position for top performers
        if percentile_rank >= self.entry_percentile:
            if self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY'
        
        # Exit long position when performance deteriorates
        elif percentile_rank <= (100 - self.exit_percentile):
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        # Exit when performance becomes neutral
        elif self.position == 'LONG' and percentile_rank <= self.exit_percentile:
            self.position = None
            return 'SELL'
        
        return 'HOLD'