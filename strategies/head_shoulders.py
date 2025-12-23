"""
Head and Shoulders Pattern Strategy

This strategy identifies head and shoulders patterns which are classic
reversal patterns indicating trend changes.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Head and Shoulders Pattern Strategy
    
    Parameters:
        lookback_period: Period to look for pattern formation (default: 50)
        tolerance: Price tolerance for pattern validation (default: 2.0%)
        min_pattern_size: Minimum pattern size as % of price (default: 5.0%)
    """
    
    def __init__(self, lookback_period=50, tolerance=2.0, min_pattern_size=5.0):
        self.lookback_period = lookback_period
        self.tolerance = tolerance
        self.min_pattern_size = min_pattern_size
        self.position = None
        self.pattern_detected = False
        self.neckline_level = None
    
    def find_peaks_and_valleys(self, highs, lows, window=5):
        """Find local peaks and valleys"""
        peaks = []
        valleys = []
        
        for i in range(window, len(highs) - window):
            # Local peak
            if all(highs[i] >= highs[j] for j in range(i - window, i + window + 1)):
                peaks.append((i, highs[i]))
            
            # Local valley
            if all(lows[i] <= lows[j] for j in range(i - window, i + window + 1)):
                valleys.append((i, lows[i]))
        
        return peaks, valleys
    
    def is_head_and_shoulders(self, peaks, valleys):
        """Check if peaks and valleys form head and shoulders pattern"""
        if len(peaks) < 3 or len(valleys) < 2:
            return False, None, None, None, None
        
        # Get last 3 peaks and 2 valleys
        recent_peaks = peaks[-3:]
        recent_valleys = valleys[-2:]
        
        # Extract peak levels
        left_shoulder = recent_peaks[0][1]
        head = recent_peaks[1][1]
        right_shoulder = recent_peaks[2][1]
        
        # Extract valley levels (neckline)
        left_valley = recent_valleys[0][1]
        right_valley = recent_valleys[1][1]
        
        # Head should be higher than both shoulders
        if not (head > left_shoulder and head > right_shoulder):
            return False, None, None, None, None
        
        # Shoulders should be approximately equal (within tolerance)
        shoulder_diff = abs(left_shoulder - right_shoulder) / max(left_shoulder, right_shoulder) * 100
        if shoulder_diff > self.tolerance:
            return False, None, None, None, None
        
        # Pattern should be significant size
        pattern_range = head - min(left_valley, right_valley)
        if pattern_range / head * 100 < self.min_pattern_size:
            return False, None, None, None, None
        
        # Calculate neckline (support level)
        neckline = (left_valley + right_valley) / 2
        
        return True, left_shoulder, head, right_shoulder, neckline
    
    def is_inverse_head_shoulders(self, peaks, valleys):
        """Check for inverse head and shoulders (bullish reversal)"""
        if len(valleys) < 3 or len(peaks) < 2:
            return False, None
        
        # Get last 3 valleys and 2 peaks
        recent_valleys = valleys[-3:]
        recent_peaks = peaks[-2:]
        
        # Extract valley levels
        left_shoulder = recent_valleys[0][1]
        head = recent_valleys[1][1]
        right_shoulder = recent_valleys[2][1]
        
        # Extract peak levels (neckline resistance)
        left_peak = recent_peaks[0][1]
        right_peak = recent_peaks[1][1]
        
        # Head should be lower than both shoulders
        if not (head < left_shoulder and head < right_shoulder):
            return False, None
        
        # Shoulders should be approximately equal
        shoulder_diff = abs(left_shoulder - right_shoulder) / max(left_shoulder, right_shoulder) * 100
        if shoulder_diff > self.tolerance:
            return False, None
        
        # Calculate neckline (resistance level)
        neckline = (left_peak + right_peak) / 2
        
        return True, neckline
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on head and shoulders pattern"""
        if len(historical_data) < self.lookback_period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        current_close = current_bar['close']
        
        # Find peaks and valleys
        peaks, valleys = self.find_peaks_and_valleys(highs, lows)
        
        # Check for head and shoulders pattern (bearish)
        is_hs, left_shoulder, head, right_shoulder, neckline = self.is_head_and_shoulders(peaks, valleys)
        
        if is_hs:
            self.pattern_detected = True
            self.neckline_level = neckline
            
            # Sell signal when price breaks below neckline
            if current_close < neckline:
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        # Check for inverse head and shoulders pattern (bullish)
        is_inv_hs, inv_neckline = self.is_inverse_head_shoulders(peaks, valleys)
        
        if is_inv_hs:
            # Buy signal when price breaks above neckline
            if current_close > inv_neckline:
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
        
        return 'HOLD'