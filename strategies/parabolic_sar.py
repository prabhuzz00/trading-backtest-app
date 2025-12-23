"""
Parabolic SAR Strategy (OPTIMIZED CONTRARIAN)

This strategy uses the Parabolic Stop and Reverse (SAR) indicator with filters to identify
high-probability reversal points. Includes minimum holding period, volume, and RSI filters
to reduce overtrading and improve win rate.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Optimized Parabolic SAR Contrarian Strategy
    
    Parameters:
        af_start: Starting acceleration factor (default: 0.01 - slower)
        af_increment: AF increment (default: 0.01 - slower) 
        af_max: Maximum AF (default: 0.1 - lower limit)
        min_distance_pct: Minimum price distance from SAR (default: 0.5%)
        min_hold_bars: Minimum holding period in bars (default: 5)
        rsi_period: RSI period for overbought/oversold filter (default: 14)
    """
    
    def __init__(self, af_start=0.01, af_increment=0.01, af_max=0.1, 
                 min_distance_pct=0.5, min_hold_bars=5, rsi_period=14, enable_short=True):
        self.af_start = af_start
        self.af_increment = af_increment
        self.af_max = af_max
        self.min_distance_pct = min_distance_pct
        self.min_hold_bars = min_hold_bars
        self.rsi_period = rsi_period
        self.enable_short = enable_short
        
        self.position = None
        self.sar = None
        self.af = af_start
        self.ep = None  # Extreme Point
        self.trend = None  # 1 for uptrend, -1 for downtrend
        self.bars_in_position = 0
        self.last_signal = None
    
    def calculate_sar(self, high, low, close):
        """Calculate Parabolic SAR for current bar"""
        if self.sar is None:
            # Initialize
            self.sar = low
            self.trend = 1
            self.ep = high
            self.af = self.af_start
            return self.sar
        
        # Calculate new SAR
        new_sar = self.sar + self.af * (self.ep - self.sar)
        
        # Check for trend reversal
        if self.trend == 1:  # Uptrend
            if low <= new_sar:
                # Trend reversal to downtrend
                self.trend = -1
                new_sar = self.ep
                self.ep = low
                self.af = self.af_start
            else:
                # Continue uptrend
                if high > self.ep:
                    self.ep = high
                    self.af = min(self.af + self.af_increment, self.af_max)
                
                # SAR should not be above previous two lows in uptrend
                new_sar = min(new_sar, low)
        
        else:  # Downtrend
            if high >= new_sar:
                # Trend reversal to uptrend
                self.trend = 1
                new_sar = self.ep
                self.ep = high
                self.af = self.af_start
            else:
                # Continue downtrend
                if low < self.ep:
                    self.ep = low
                    self.af = min(self.af + self.af_increment, self.af_max)
                
                # SAR should not be below previous two highs in downtrend
                new_sar = max(new_sar, high)
        
        self.sar = new_sar
        return self.sar
    
    def calculate_rsi(self, historical_data, period=14):
        """Calculate RSI indicator"""
        if len(historical_data) < period + 1:
            return 50  # Neutral RSI
        
        closes = historical_data['close'].values[-period-1:]
        deltas = np.diff(closes)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def check_volume_surge(self, historical_data):
        """Check if current volume is above average (confirms strength)"""
        if len(historical_data) < 20 or 'volume' not in historical_data.columns:
            return True  # Skip filter if not enough data
        
        current_volume = historical_data['volume'].iloc[-1]
        avg_volume = historical_data['volume'].iloc[-20:].mean()
        
        # Require volume to be at least 80% of average
        return current_volume >= (avg_volume * 0.8)
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Parabolic SAR with filters"""
        if len(historical_data) < max(self.rsi_period + 5, 25):
            return 'HOLD'
        
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Calculate current SAR
        sar_value = self.calculate_sar(current_high, current_low, current_close)
        
        # Calculate RSI for overbought/oversold filter
        rsi = self.calculate_rsi(historical_data, self.rsi_period)
        
        # Check volume
        volume_ok = self.check_volume_surge(historical_data)
        
        # Calculate distance from SAR (as percentage)
        distance_pct = abs(current_close - sar_value) / sar_value * 100
        
        # Increment holding period counter
        if self.position in ['LONG', 'SHORT']:
            self.bars_in_position += 1
        else:
            self.bars_in_position = 0
        
        # Generate signals based on price vs SAR with MULTIPLE FILTERS
        if current_close < sar_value and self.trend == -1:
            # Price below SAR in downtrend - potential buy signal (contrarian)
            if self.position == 'SHORT':
                # Close short position
                if self.bars_in_position >= self.min_hold_bars:
                    self.position = None
                    self.bars_in_position = 0
                    self.last_signal = 'BUY_SHORT'
                    return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Apply filters:
                # 1. RSI should show oversold conditions (< 40)
                # 2. Price should be far enough from SAR
                # 3. Volume should be decent
                if rsi < 40 and distance_pct >= self.min_distance_pct and volume_ok:
                    self.position = 'LONG'
                    self.bars_in_position = 0
                    self.last_signal = 'BUY_LONG'
                    return 'BUY_LONG'
        
        elif current_close > sar_value and self.trend == 1:
            # Price above SAR in uptrend - potential sell signal (contrarian)
            if self.position == 'LONG':
                # Apply filters:
                # 1. Must hold for minimum bars
                # 2. RSI should show overbought conditions (> 60) OR stopped out
                # 3. Price should be far enough from SAR OR minimum hold met
                if self.bars_in_position >= self.min_hold_bars:
                    if rsi > 60 or distance_pct >= self.min_distance_pct:
                        self.position = None
                        self.bars_in_position = 0
                        self.last_signal = 'SELL_LONG'
                        return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Apply filters for short entry
                if rsi > 60 and distance_pct >= self.min_distance_pct and volume_ok:
                    self.position = 'SHORT'
                    self.bars_in_position = 0
                    self.last_signal = 'SELL_SHORT'
                    return 'SELL_SHORT'
        
        return 'HOLD'