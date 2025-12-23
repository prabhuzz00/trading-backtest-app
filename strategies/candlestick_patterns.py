"""
Candlestick Pattern Recognition Strategy

This strategy identifies various candlestick patterns and generates
trading signals based on their bullish or bearish implications.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Candlestick Pattern Recognition Strategy
    
    Parameters:
        min_body_size: Minimum body size as % of total range (default: 0.3)
        doji_threshold: Maximum body size for doji pattern (default: 0.1)
        shadow_ratio: Minimum shadow to body ratio for certain patterns (default: 2.0)
    """
    
    def __init__(self, min_body_size=0.3, doji_threshold=0.1, shadow_ratio=2.0):
        self.min_body_size = min_body_size
        self.doji_threshold = doji_threshold
        self.shadow_ratio = shadow_ratio
        self.position = None
    
    def get_candle_metrics(self, open_price, high, low, close):
        """Calculate candle metrics"""
        body = abs(close - open_price)
        total_range = high - low
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        
        return body, total_range, upper_shadow, lower_shadow
    
    def is_doji(self, open_price, high, low, close):
        """Identify doji pattern"""
        body, total_range, _, _ = self.get_candle_metrics(open_price, high, low, close)
        
        if total_range == 0:
            return False
        
        return (body / total_range) <= self.doji_threshold
    
    def is_hammer(self, open_price, high, low, close):
        """Identify hammer pattern (bullish reversal)"""
        body, total_range, upper_shadow, lower_shadow = self.get_candle_metrics(
            open_price, high, low, close)
        
        if body == 0 or total_range == 0:
            return False
        
        # Hammer: long lower shadow, small upper shadow, small body
        return (lower_shadow >= body * self.shadow_ratio and
                upper_shadow <= total_range * 0.1 and
                body / total_range >= 0.1)
    
    def is_shooting_star(self, open_price, high, low, close):
        """Identify shooting star pattern (bearish reversal)"""
        body, total_range, upper_shadow, lower_shadow = self.get_candle_metrics(
            open_price, high, low, close)
        
        if body == 0 or total_range == 0:
            return False
        
        # Shooting star: long upper shadow, small lower shadow, small body
        return (upper_shadow >= body * self.shadow_ratio and
                lower_shadow <= total_range * 0.1 and
                body / total_range >= 0.1)
    
    def is_engulfing_bullish(self, prev_open, prev_high, prev_low, prev_close,
                            curr_open, curr_high, curr_low, curr_close):
        """Identify bullish engulfing pattern"""
        # Previous candle should be bearish
        if prev_close >= prev_open:
            return False
        
        # Current candle should be bullish
        if curr_close <= curr_open:
            return False
        
        # Current candle should engulf previous candle's body
        return (curr_open < prev_close and curr_close > prev_open)
    
    def is_engulfing_bearish(self, prev_open, prev_high, prev_low, prev_close,
                            curr_open, curr_high, curr_low, curr_close):
        """Identify bearish engulfing pattern"""
        # Previous candle should be bullish
        if prev_close <= prev_open:
            return False
        
        # Current candle should be bearish
        if curr_close >= curr_open:
            return False
        
        # Current candle should engulf previous candle's body
        return (curr_open > prev_close and curr_close < prev_open)
    
    def is_piercing_line(self, prev_open, prev_high, prev_low, prev_close,
                        curr_open, curr_high, curr_low, curr_close):
        """Identify piercing line pattern (bullish reversal)"""
        # Previous candle should be bearish
        if prev_close >= prev_open:
            return False
        
        # Current candle should be bullish
        if curr_close <= curr_open:
            return False
        
        # Current candle should open below previous low and close above midpoint
        prev_midpoint = (prev_open + prev_close) / 2
        return (curr_open < prev_low and curr_close > prev_midpoint)
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on candlestick patterns"""
        if len(historical_data) < 2:
            return 'HOLD'
        
        # Current bar data
        curr_open = current_bar['open']
        curr_high = current_bar['high']
        curr_low = current_bar['low']
        curr_close = current_bar['close']
        
        # Previous bar data
        prev_data = historical_data.iloc[-1]
        prev_open = prev_data['open']
        prev_high = prev_data['high']
        prev_low = prev_data['low']
        prev_close = prev_data['close']
        
        # Check for bullish patterns
        bullish_signals = []
        
        if self.is_hammer(curr_open, curr_high, curr_low, curr_close):
            bullish_signals.append('hammer')
        
        if self.is_engulfing_bullish(prev_open, prev_high, prev_low, prev_close,
                                   curr_open, curr_high, curr_low, curr_close):
            bullish_signals.append('bullish_engulfing')
        
        if self.is_piercing_line(prev_open, prev_high, prev_low, prev_close,
                               curr_open, curr_high, curr_low, curr_close):
            bullish_signals.append('piercing_line')
        
        # Check for bearish patterns
        bearish_signals = []
        
        if self.is_shooting_star(curr_open, curr_high, curr_low, curr_close):
            bearish_signals.append('shooting_star')
        
        if self.is_engulfing_bearish(prev_open, prev_high, prev_low, prev_close,
                                   curr_open, curr_high, curr_low, curr_close):
            bearish_signals.append('bearish_engulfing')
        
        # Generate trading signals
        
        # Buy on bullish patterns
        if bullish_signals and not bearish_signals:
            if self.position != 'LONG':
                self.position = 'LONG'
                return 'BUY'
        
        # Sell on bearish patterns
        elif bearish_signals and not bullish_signals:
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        # Doji at key levels (indecision)
        elif self.is_doji(curr_open, curr_high, curr_low, curr_close):
            # Exit position on doji (indecision)
            if self.position == 'LONG':
                self.position = None
                return 'SELL'
        
        return 'HOLD'