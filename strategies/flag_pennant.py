"""
Flag and Pennant Pattern Strategy

This strategy identifies flag and pennant continuation patterns
and trades in the direction of the prevailing trend after consolidation.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Flag and Pennant Pattern Strategy
    
    Parameters:
        trend_period: Period to identify prevailing trend (default: 20)
        pattern_period: Maximum pattern formation period (default: 15)
        min_trend_strength: Minimum trend strength % (default: 5.0%)
        breakout_threshold: Breakout confirmation threshold (default: 1.0%)
    """
    
    def __init__(self, trend_period=20, pattern_period=15, 
                 min_trend_strength=5.0, breakout_threshold=1.0):
        self.trend_period = trend_period
        self.pattern_period = pattern_period
        self.min_trend_strength = min_trend_strength
        self.breakout_threshold = breakout_threshold
        self.position = None
    
    def identify_trend_direction(self, closes):
        """Identify the prevailing trend direction"""
        if len(closes) < self.trend_period:
            return None, 0
        
        trend_start = closes[-self.trend_period]
        trend_end = closes[-1]
        
        if trend_start == 0:
            return None, 0
        
        trend_strength = (trend_end - trend_start) / trend_start * 100
        
        if trend_strength >= self.min_trend_strength:
            return 'uptrend', trend_strength
        elif trend_strength <= -self.min_trend_strength:
            return 'downtrend', abs(trend_strength)
        else:
            return None, 0
    
    def is_flag_pattern(self, highs, lows, trend_direction):
        """Check for flag pattern (rectangular consolidation)"""
        if len(highs) < 5 or trend_direction is None:
            return False, None, None
        
        # Flag should be relatively short
        if len(highs) > self.pattern_period:
            return False, None, None
        
        # Calculate consolidation range
        pattern_high = np.max(highs)
        pattern_low = np.min(lows)
        pattern_range = pattern_high - pattern_low
        
        # Flag should have relatively tight range (< 3% of price)
        if pattern_range / pattern_high * 100 > 3.0:
            return False, None, None
        
        # Flag should slope against the trend (or be horizontal)
        if len(highs) >= 3:
            early_avg = np.mean(highs[:len(highs)//2])
            late_avg = np.mean(highs[len(highs)//2:])
            
            slope_direction = 'up' if late_avg > early_avg else 'down'
            
            # In uptrend, flag should slope down or sideways
            # In downtrend, flag should slope up or sideways
            if trend_direction == 'uptrend' and slope_direction == 'up':
                return False, None, None
            elif trend_direction == 'downtrend' and slope_direction == 'down':
                return False, None, None
        
        return True, pattern_high, pattern_low
    
    def is_pennant_pattern(self, highs, lows, trend_direction):
        """Check for pennant pattern (triangular consolidation)"""
        if len(highs) < 5 or trend_direction is None:
            return False, None, None
        
        # Pennant should be relatively short
        if len(highs) > self.pattern_period:
            return False, None, None
        
        # Find trend lines for pennant
        # Upper trend line (connecting highs)
        high_points = []
        for i, high in enumerate(highs):
            if i == 0 or i == len(highs) - 1:
                high_points.append((i, high))
            elif high >= max(highs[max(0, i-2):i+3]):
                high_points.append((i, high))
        
        # Lower trend line (connecting lows)
        low_points = []
        for i, low in enumerate(lows):
            if i == 0 or i == len(lows) - 1:
                low_points.append((i, low))
            elif low <= min(lows[max(0, i-2):i+3]):
                low_points.append((i, low))
        
        if len(high_points) < 2 or len(low_points) < 2:
            return False, None, None
        
        # Check if trend lines are converging
        if len(high_points) >= 2 and len(low_points) >= 2:
            high_slope = (high_points[-1][1] - high_points[0][1]) / (high_points[-1][0] - high_points[0][0])
            low_slope = (low_points[-1][1] - low_points[0][1]) / (low_points[-1][0] - low_points[0][0])
            
            # Lines should be converging
            if high_slope > 0 and low_slope > 0:  # Both rising
                return False, None, None
            elif high_slope < 0 and low_slope < 0:  # Both falling
                return False, None, None
        
        pattern_high = np.max(highs)
        pattern_low = np.min(lows)
        
        return True, pattern_high, pattern_low
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on flag/pennant breakouts"""
        if len(historical_data) < self.trend_period + self.pattern_period:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        # Identify prevailing trend
        trend_direction, trend_strength = self.identify_trend_direction(closes)
        
        if trend_direction is None:
            return 'HOLD'
        
        # Analyze recent price action for pattern
        pattern_start = max(5, min(self.pattern_period, len(historical_data) // 4))
        recent_highs = historical_data['high'].values[-pattern_start:]
        recent_lows = historical_data['low'].values[-pattern_start:]
        
        # Check for flag pattern
        is_flag, flag_high, flag_low = self.is_flag_pattern(recent_highs, recent_lows, trend_direction)
        
        # Check for pennant pattern
        is_pennant, pennant_high, pennant_low = self.is_pennant_pattern(recent_highs, recent_lows, trend_direction)
        
        if not (is_flag or is_pennant):
            return 'HOLD'
        
        # Use flag or pennant levels
        pattern_high = flag_high if is_flag else pennant_high
        pattern_low = flag_low if is_flag else pennant_low
        
        if pattern_high is None or pattern_low is None:
            return 'HOLD'
        
        # Calculate breakout levels
        pattern_range = pattern_high - pattern_low
        breakout_distance = pattern_range * (self.breakout_threshold / 100)
        
        # Generate signals in trend direction
        if trend_direction == 'uptrend':
            # Buy on upward breakout from pattern
            if current_high > pattern_high + breakout_distance:
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
        
        elif trend_direction == 'downtrend':
            # Sell on downward breakout from pattern (or exit long)
            if current_low < pattern_low - breakout_distance:
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        # Stop loss: exit if breakout fails and price reverses
        if self.position == 'LONG':
            if trend_direction == 'uptrend' and current_close < pattern_low:
                self.position = None
                return 'SELL'
        
        return 'HOLD'