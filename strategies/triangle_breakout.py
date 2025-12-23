"""
Triangle Pattern Breakout Strategy

This strategy identifies triangle patterns (ascending, descending, symmetric)
and trades breakouts from these consolidation patterns.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Triangle Pattern Breakout Strategy
    
    Parameters:
        min_pattern_length: Minimum bars for pattern formation (default: 20)
        max_pattern_length: Maximum bars for pattern formation (default: 50)
        breakout_threshold: Percentage breakout confirmation (default: 1.0%)
        trend_line_touches: Minimum touches for trend line validation (default: 3)
    """
    
    def __init__(self, min_pattern_length=20, max_pattern_length=50, 
                 breakout_threshold=1.0, trend_line_touches=3):
        self.min_pattern_length = min_pattern_length
        self.max_pattern_length = max_pattern_length
        self.breakout_threshold = breakout_threshold
        self.trend_line_touches = trend_line_touches
        self.position = None
    
    def find_trend_line(self, points, is_ascending=True):
        """Find trend line through given points"""
        if len(points) < 2:
            return None, None
        
        # Extract x and y coordinates
        x_coords = np.array([p[0] for p in points])
        y_coords = np.array([p[1] for p in points])
        
        # Fit linear trend line
        slope, intercept = np.polyfit(x_coords, y_coords, 1)
        
        # Validate trend line direction
        if is_ascending and slope <= 0:
            return None, None
        elif not is_ascending and slope >= 0:
            return None, None
        
        return slope, intercept
    
    def get_trend_line_touches(self, highs, lows, slope, intercept, is_resistance=True):
        """Count how many times price touches the trend line"""
        touches = 0
        tolerance = 0.5  # 0.5% tolerance
        
        data = highs if is_resistance else lows
        
        for i, price in enumerate(data):
            trend_line_value = slope * i + intercept
            
            if trend_line_value > 0:
                deviation = abs(price - trend_line_value) / trend_line_value * 100
                if deviation <= tolerance:
                    touches += 1
        
        return touches
    
    def identify_triangle_pattern(self, highs, lows):
        """Identify triangle patterns"""
        if len(highs) < self.min_pattern_length:
            return None, None, None, None
        
        # Find significant highs and lows for pattern analysis
        window = 3
        significant_highs = []
        significant_lows = []
        
        # Find local extrema
        for i in range(window, len(highs) - window):
            # Local high
            if all(highs[i] >= highs[j] for j in range(i - window, i + window + 1)):
                significant_highs.append((i, highs[i]))
            
            # Local low
            if all(lows[i] <= lows[j] for j in range(i - window, i + window + 1)):
                significant_lows.append((i, lows[i]))
        
        if len(significant_highs) < 2 or len(significant_lows) < 2:
            return None, None, None, None
        
        # Try to fit trend lines
        # Resistance line (connecting highs)
        resistance_slope, resistance_intercept = self.find_trend_line(
            significant_highs[-4:] if len(significant_highs) >= 4 else significant_highs,
            is_ascending=False)
        
        # Support line (connecting lows)
        support_slope, support_intercept = self.find_trend_line(
            significant_lows[-4:] if len(significant_lows) >= 4 else significant_lows,
            is_ascending=True)
        
        # Validate trend lines
        if resistance_slope is None or support_slope is None:
            return None, None, None, None
        
        # Check for sufficient touches
        resistance_touches = self.get_trend_line_touches(
            highs, lows, resistance_slope, resistance_intercept, is_resistance=True)
        support_touches = self.get_trend_line_touches(
            highs, lows, support_slope, support_intercept, is_resistance=False)
        
        if (resistance_touches < self.trend_line_touches or 
            support_touches < self.trend_line_touches):
            return None, None, None, None
        
        # Determine triangle type
        if resistance_slope < 0 and support_slope > 0:
            if abs(resistance_slope) > abs(support_slope):
                pattern_type = 'ascending'
            elif abs(support_slope) > abs(resistance_slope):
                pattern_type = 'descending'
            else:
                pattern_type = 'symmetric'
        else:
            pattern_type = 'invalid'
        
        return pattern_type, resistance_slope, resistance_intercept, support_slope, support_intercept
    
    def calculate_breakout_levels(self, current_index, resistance_slope, resistance_intercept,
                                 support_slope, support_intercept):
        """Calculate current support and resistance levels"""
        if None in [resistance_slope, resistance_intercept, support_slope, support_intercept]:
            return None, None
        
        resistance_level = resistance_slope * current_index + resistance_intercept
        support_level = support_slope * current_index + support_intercept
        
        return resistance_level, support_level
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on triangle breakouts"""
        if len(historical_data) < self.min_pattern_length:
            return 'HOLD'
        
        # Use recent data for pattern detection
        recent_length = min(self.max_pattern_length, len(historical_data))
        recent_highs = historical_data['high'].values[-recent_length:]
        recent_lows = historical_data['low'].values[-recent_length:]
        
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Identify triangle pattern
        pattern_result = self.identify_triangle_pattern(recent_highs, recent_lows)
        pattern_type, res_slope, res_intercept, sup_slope, sup_intercept = pattern_result
        
        if pattern_type is None or pattern_type == 'invalid':
            return 'HOLD'
        
        # Calculate current breakout levels
        current_index = len(recent_highs) - 1
        resistance_level, support_level = self.calculate_breakout_levels(
            current_index, res_slope, res_intercept, sup_slope, sup_intercept)
        
        if resistance_level is None or support_level is None:
            return 'HOLD'
        
        # Calculate breakout thresholds
        breakout_distance = (resistance_level - support_level) * (self.breakout_threshold / 100)
        
        # Generate signals based on breakouts
        
        # Upward breakout
        if current_high > resistance_level + breakout_distance:
            if self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY'
        
        # Downward breakout
        elif current_low < support_level - breakout_distance:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        return 'HOLD'