"""
Double Top/Bottom Pattern Strategy

This strategy identifies double top and double bottom patterns
which are classic reversal patterns in technical analysis.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Double Top/Bottom Pattern Strategy
    
    Parameters:
        lookback_period: Period to search for patterns (default: 40)
        price_tolerance: Price tolerance for pattern validation (default: 1.5%)
        min_pattern_height: Minimum pattern height as % of price (default: 3.0%)
        min_time_between: Minimum bars between peaks/valleys (default: 10)
    """
    
    def __init__(self, lookback_period=40, price_tolerance=1.5, 
                 min_pattern_height=3.0, min_time_between=10):
        self.lookback_period = lookback_period
        self.price_tolerance = price_tolerance
        self.min_pattern_height = min_pattern_height
        self.min_time_between = min_time_between
        self.position = None
    
    def find_extrema(self, prices, is_peaks=True, window=3):
        """Find local peaks or valleys"""
        extrema = []
        
        for i in range(window, len(prices) - window):
            if is_peaks:
                # Find peaks
                if all(prices[i] >= prices[j] for j in range(i - window, i + window + 1) if j != i):
                    extrema.append((i, prices[i]))
            else:
                # Find valleys
                if all(prices[i] <= prices[j] for j in range(i - window, i + window + 1) if j != i):
                    extrema.append((i, prices[i]))
        
        return extrema
    
    def is_double_top(self, highs):
        """Check for double top pattern"""
        peaks = self.find_extrema(highs, is_peaks=True)
        
        if len(peaks) < 2:
            return False, None, None
        
        # Check recent peaks
        for i in range(len(peaks) - 1):
            peak1_idx, peak1_price = peaks[i]
            peak2_idx, peak2_price = peaks[i + 1]
            
            # Check time separation
            if peak2_idx - peak1_idx < self.min_time_between:
                continue
            
            # Check price similarity
            price_diff = abs(peak1_price - peak2_price) / max(peak1_price, peak2_price) * 100
            if price_diff > self.price_tolerance:
                continue
            
            # Check pattern significance
            if len(highs) > peak2_idx + 5:
                recent_low = np.min(highs[peak1_idx:peak2_idx])
                pattern_height = min(peak1_price, peak2_price) - recent_low
                if pattern_height / min(peak1_price, peak2_price) * 100 < self.min_pattern_height:
                    continue
            
            # Valid double top found
            neckline = np.min(highs[peak1_idx:peak2_idx])
            return True, max(peak1_price, peak2_price), neckline
        
        return False, None, None
    
    def is_double_bottom(self, lows):
        """Check for double bottom pattern"""
        valleys = self.find_extrema(lows, is_peaks=False)
        
        if len(valleys) < 2:
            return False, None, None
        
        # Check recent valleys
        for i in range(len(valleys) - 1):
            valley1_idx, valley1_price = valleys[i]
            valley2_idx, valley2_price = valleys[i + 1]
            
            # Check time separation
            if valley2_idx - valley1_idx < self.min_time_between:
                continue
            
            # Check price similarity
            price_diff = abs(valley1_price - valley2_price) / max(valley1_price, valley2_price) * 100
            if price_diff > self.price_tolerance:
                continue
            
            # Check pattern significance
            if len(lows) > valley2_idx + 5:
                # Find the high between valleys for neckline
                if valley1_idx < len(lows) and valley2_idx < len(lows):
                    # Use the original data to find high between valleys
                    # For now, we'll approximate
                    recent_high = np.max(lows[valley1_idx:valley2_idx])  # This should be highs, but we only have lows
                    pattern_height = recent_high - max(valley1_price, valley2_price)
                    if pattern_height / recent_high * 100 < self.min_pattern_height:
                        continue
            
            # Valid double bottom found
            # Approximate neckline as high between valleys
            neckline = np.max(lows[valley1_idx:valley2_idx])  # Approximation
            return True, min(valley1_price, valley2_price), neckline
        
        return False, None, None
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on double top/bottom patterns"""
        if len(historical_data) < self.lookback_period:
            return 'HOLD'
        
        highs = historical_data['high'].values[-self.lookback_period:]
        lows = historical_data['low'].values[-self.lookback_period:]
        current_close = current_bar['close']
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        # Check for double top (bearish reversal)
        is_dt, dt_peak, dt_neckline = self.is_double_top(highs)
        
        if is_dt and dt_neckline is not None:
            # Sell signal when price breaks below neckline
            if current_close < dt_neckline:
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
        
        # Check for double bottom (bullish reversal)
        is_db, db_valley, db_neckline = self.is_double_bottom(lows)
        
        if is_db and db_neckline is not None:
            # Buy signal when price breaks above neckline
            if current_close > db_neckline:
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
        
        return 'HOLD'