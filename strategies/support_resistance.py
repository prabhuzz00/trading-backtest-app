"""
Support and Resistance Strategy

This strategy identifies key support and resistance levels and trades
bounces off these levels, assuming price will reverse at these points.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Support and Resistance Strategy
    
    Parameters:
        lookback_period: Period to identify S&R levels (default: 50)
        min_touches: Minimum touches to validate level (default: 2)
        proximity_threshold: % proximity to consider touching level (default: 0.5)
    """
    
    def __init__(self, lookback_period=50, min_touches=2, proximity_threshold=0.5, enable_short=True):
        self.lookback_period = lookback_period
        self.min_touches = min_touches
        self.proximity_threshold = proximity_threshold
        self.enable_short = enable_short
        self.position = None
        self.support_levels = []
        self.resistance_levels = []
    
    def identify_support_resistance_levels(self, highs, lows, closes):
        """Identify support and resistance levels"""
        if len(closes) < self.lookback_period:
            return [], []
        
        # Find local minima (potential support) and maxima (potential resistance)
        support_candidates = []
        resistance_candidates = []
        
        window = 5  # Window for local extrema
        
        for i in range(window, len(closes) - window):
            # Local minimum (support)
            if all(lows[i] <= lows[j] for j in range(i - window, i + window + 1)):
                support_candidates.append(lows[i])
            
            # Local maximum (resistance)
            if all(highs[i] >= highs[j] for j in range(i - window, i + window + 1)):
                resistance_candidates.append(highs[i])
        
        # Validate levels by counting touches
        validated_support = []
        validated_resistance = []
        
        for level in support_candidates:
            touches = sum(1 for price in lows if abs(price - level) / level * 100 <= self.proximity_threshold)
            if touches >= self.min_touches:
                validated_support.append(level)
        
        for level in resistance_candidates:
            touches = sum(1 for price in highs if abs(price - level) / level * 100 <= self.proximity_threshold)
            if touches >= self.min_touches:
                validated_resistance.append(level)
        
        return validated_support, validated_resistance
    
    def find_nearest_levels(self, current_price, support_levels, resistance_levels):
        """Find nearest support and resistance levels"""
        nearest_support = None
        nearest_resistance = None
        
        # Find nearest support below current price
        valid_supports = [s for s in support_levels if s < current_price]
        if valid_supports:
            nearest_support = max(valid_supports)
        
        # Find nearest resistance above current price
        valid_resistances = [r for r in resistance_levels if r > current_price]
        if valid_resistances:
            nearest_resistance = min(valid_resistances)
        
        return nearest_support, nearest_resistance
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on support/resistance bounces"""
        if len(historical_data) < self.lookback_period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        current_price = current_bar['close']
        current_low = current_bar['low']
        current_high = current_bar['high']
        
        # Update S&R levels
        self.support_levels, self.resistance_levels = self.identify_support_resistance_levels(
            highs, lows, closes)
        
        # Find nearest levels
        nearest_support, nearest_resistance = self.find_nearest_levels(
            current_price, self.support_levels, self.resistance_levels)
        
        # Trading logic
        # Buy at support bounce
        if nearest_support is not None:
            distance_to_support = abs(current_low - nearest_support) / nearest_support * 100
            if distance_to_support <= self.proximity_threshold:
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    return 'BUY_LONG'
        
        # Sell at resistance rejection
        if nearest_resistance is not None:
            distance_to_resistance = abs(current_high - nearest_resistance) / nearest_resistance * 100
            if distance_to_resistance <= self.proximity_threshold:
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    return 'SELL_SHORT'
        
        return 'HOLD'