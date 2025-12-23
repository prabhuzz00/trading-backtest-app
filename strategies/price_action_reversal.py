"""
Price Action Reversal Strategy

This strategy identifies reversal patterns based on price action signals
such as hammer/doji candlesticks at support/resistance levels.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Price Action Reversal Strategy
    
    Parameters:
        doji_threshold: Max body/range ratio for doji (default: 0.1)
        hammer_ratio: Min lower shadow/body ratio for hammer (default: 2.0)
        min_range_pct: Minimum range as % of price for valid pattern (default: 0.5)
    """
    
    def __init__(self, doji_threshold=0.1, hammer_ratio=2.0, min_range_pct=0.5):
        self.doji_threshold = doji_threshold
        self.hammer_ratio = hammer_ratio
        self.min_range_pct = min_range_pct
        self.position = None
    
    def is_doji(self, open_price, high, low, close):
        """Check if candlestick is a doji"""
        body = abs(close - open_price)
        total_range = high - low
        
        if total_range == 0:
            return False
        
        # Doji: very small body relative to total range
        body_ratio = body / total_range
        return body_ratio <= self.doji_threshold
    
    def is_hammer(self, open_price, high, low, close):
        """Check if candlestick is a hammer (bullish reversal)"""
        body = abs(close - open_price)
        lower_shadow = min(open_price, close) - low
        upper_shadow = high - max(open_price, close)
        total_range = high - low
        
        if body == 0 or total_range == 0:
            return False
        
        # Hammer: long lower shadow, small body, small upper shadow
        lower_shadow_ratio = lower_shadow / body if body > 0 else 0
        upper_shadow_ratio = upper_shadow / total_range
        
        return (lower_shadow_ratio >= self.hammer_ratio and 
                upper_shadow_ratio <= 0.3 and
                total_range / close * 100 >= self.min_range_pct)
    
    def is_shooting_star(self, open_price, high, low, close):
        """Check if candlestick is a shooting star (bearish reversal)"""
        body = abs(close - open_price)
        lower_shadow = min(open_price, close) - low
        upper_shadow = high - max(open_price, close)
        total_range = high - low
        
        if body == 0 or total_range == 0:
            return False
        
        # Shooting star: long upper shadow, small body, small lower shadow
        upper_shadow_ratio = upper_shadow / body if body > 0 else 0
        lower_shadow_ratio = lower_shadow / total_range
        
        return (upper_shadow_ratio >= self.hammer_ratio and 
                lower_shadow_ratio <= 0.3 and
                total_range / close * 100 >= self.min_range_pct)
    
    def is_near_support_resistance(self, current_price, historical_data):
        """Check if current price is near support/resistance"""
        if len(historical_data) < 20:
            return False, False
        
        highs = historical_data['high'].values[-20:]
        lows = historical_data['low'].values[-20:]
        
        # Simple S&R: recent highs and lows
        resistance_level = np.max(highs)
        support_level = np.min(lows)
        
        price_range = resistance_level - support_level
        if price_range == 0:
            return False, False
        
        # Check if within 2% of support/resistance
        near_resistance = abs(current_price - resistance_level) / resistance_level <= 0.02
        near_support = abs(current_price - support_level) / support_level <= 0.02
        
        return near_support, near_resistance
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on reversal patterns"""
        if len(historical_data) < 20:
            return 'HOLD'
        
        # Current bar data
        open_price = current_bar['open']
        high = current_bar['high']
        low = current_bar['low']
        close = current_bar['close']
        
        # Check for reversal patterns
        is_doji_pattern = self.is_doji(open_price, high, low, close)
        is_hammer_pattern = self.is_hammer(open_price, high, low, close)
        is_shooting_star_pattern = self.is_shooting_star(open_price, high, low, close)
        
        # Check proximity to support/resistance
        near_support, near_resistance = self.is_near_support_resistance(close, historical_data)
        
        # Generate signals
        
        # Bullish reversal signals
        if (is_hammer_pattern or (is_doji_pattern and near_support)):
            if self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY'
        
        # Bearish reversal signals
        elif (is_shooting_star_pattern or (is_doji_pattern and near_resistance)):
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        return 'HOLD'