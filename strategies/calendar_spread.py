"""
Calendar Spread Strategy

This strategy exploits price differences between different time periods
or expiration dates. Simplified version using seasonal patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class Strategy:
    """
    Calendar Spread Strategy (Simplified Seasonal)
    
    Parameters:
        seasonal_period: Period for seasonal analysis (default: 252 trading days)
        lookback_years: Years of data for seasonal pattern (default: 3)
        seasonal_threshold: Threshold for seasonal signal (default: 1.5)
    """
    
    def __init__(self, seasonal_period=252, lookback_years=3, seasonal_threshold=1.5):
        self.seasonal_period = seasonal_period
        self.lookback_years = lookback_years
        self.seasonal_threshold = seasonal_threshold
        self.position = None
        self.historical_returns = {}
    
    def get_day_of_year(self, date_str=None):
        """Get day of year (1-365/366)"""
        if date_str is None:
            # Use current date if not provided
            return datetime.now().timetuple().tm_yday
        
        try:
            # Try to parse date string
            date_obj = pd.to_datetime(date_str)
            return date_obj.timetuple().tm_yday
        except:
            # Fallback to current day
            return datetime.now().timetuple().tm_yday
    
    def calculate_seasonal_pattern(self, historical_data):
        """Calculate seasonal return patterns"""
        if len(historical_data) < self.seasonal_period:
            return None
        
        # Group returns by day of year
        seasonal_returns = {}
        
        # Calculate daily returns
        closes = historical_data['close'].values
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] != 0:
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(ret)
        
        # Simulate seasonal grouping (in real implementation, would use actual dates)
        # For demonstration, we'll use position in year as a proxy
        days_per_chunk = len(returns) // min(self.lookback_years, 3)
        
        for i, ret in enumerate(returns[-self.seasonal_period:]):
            # Approximate day of year based on position
            approx_day = (i % 252) + 1  # Assuming 252 trading days per year
            
            if approx_day not in seasonal_returns:
                seasonal_returns[approx_day] = []
            
            seasonal_returns[approx_day].append(ret)
        
        # Calculate average return for each day
        seasonal_averages = {}
        for day, day_returns in seasonal_returns.items():
            if len(day_returns) >= 2:  # Need at least 2 observations
                seasonal_averages[day] = np.mean(day_returns)
        
        return seasonal_averages
    
    def get_seasonal_expectation(self, seasonal_patterns, current_day):
        """Get seasonal expectation for current day"""
        if seasonal_patterns is None or current_day not in seasonal_patterns:
            return 0
        
        # Get current day expectation
        current_expectation = seasonal_patterns[current_day]
        
        # Also consider nearby days (smooth the pattern)
        nearby_days = []
        for day_offset in range(-5, 6):  # +/- 5 days
            day = current_day + day_offset
            if day in seasonal_patterns:
                nearby_days.append(seasonal_patterns[day])
        
        if nearby_days:
            smoothed_expectation = np.mean(nearby_days)
            # Weight current day more heavily
            final_expectation = 0.7 * current_expectation + 0.3 * smoothed_expectation
        else:
            final_expectation = current_expectation
        
        return final_expectation
    
    def calculate_momentum_adjustment(self, closes):
        """Adjust seasonal signal based on recent momentum"""
        if len(closes) < 10:
            return 1.0
        
        # Calculate recent momentum
        recent_return = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
        
        # Adjust seasonal signal based on momentum
        # If momentum aligns with seasonal pattern, strengthen signal
        # If momentum opposes seasonal pattern, weaken signal
        momentum_factor = 1 + (recent_return * 10)  # Scale factor
        
        return max(0.5, min(2.0, momentum_factor))  # Clamp to reasonable range
    
    def generate_signal(self, current_bar, historical_data):
        """Generate calendar spread signals based on seasonal patterns"""
        if len(historical_data) < self.seasonal_period:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        
        # Calculate seasonal patterns
        seasonal_patterns = self.calculate_seasonal_pattern(historical_data)
        
        if seasonal_patterns is None:
            return 'HOLD'
        
        # Get current day of year (approximated)
        current_day = (len(closes) % 252) + 1
        
        # Get seasonal expectation
        seasonal_expectation = self.get_seasonal_expectation(seasonal_patterns, current_day)
        
        # Calculate momentum adjustment
        momentum_factor = self.calculate_momentum_adjustment(closes)
        
        # Adjust seasonal signal
        adjusted_expectation = seasonal_expectation * momentum_factor
        
        # Generate trading signals
        
        # Strong positive seasonal expectation
        if adjusted_expectation >= self.seasonal_threshold / 100:
            if self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY'
        
        # Strong negative seasonal expectation
        elif adjusted_expectation <= -self.seasonal_threshold / 100:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        # Neutral expectation - exit positions
        elif abs(adjusted_expectation) < (self.seasonal_threshold / 2) / 100:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        return 'HOLD'