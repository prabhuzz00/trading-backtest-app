"""
Ichimoku Cloud Strategy

This strategy uses the Ichimoku Kinko Hyo indicator system which includes
Tenkan-sen, Kijun-sen, Senkou Span A & B, and Chikou Span to identify
trend direction and momentum.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Ichimoku Cloud Strategy
    
    Parameters:
        tenkan_period: Tenkan-sen period (default: 9)
        kijun_period: Kijun-sen period (default: 26)
        senkou_b_period: Senkou Span B period (default: 52)
    """
    
    def __init__(self, tenkan_period=9, kijun_period=26, senkou_b_period=52, enable_short=True):
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.enable_short = enable_short
        self.position = None
    
    def calculate_ichimoku(self, highs, lows, closes):
        """Calculate Ichimoku components"""
        if len(closes) < self.senkou_b_period:
            return None, None, None, None, None
        
        # Tenkan-sen (Conversion Line)
        tenkan_high = np.max(highs[-self.tenkan_period:])
        tenkan_low = np.min(lows[-self.tenkan_period:])
        tenkan_sen = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line)
        kijun_high = np.max(highs[-self.kijun_period:])
        kijun_low = np.min(lows[-self.kijun_period:])
        kijun_sen = (kijun_high + kijun_low) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        
        # Senkou Span B (Leading Span B)
        senkou_b_high = np.max(highs[-self.senkou_b_period:])
        senkou_b_low = np.min(lows[-self.senkou_b_period:])
        senkou_span_b = (senkou_b_high + senkou_b_low) / 2
        
        # Chikou Span (Lagging Span) - current close displaced back
        chikou_span = closes[-1]
        
        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on Ichimoku Cloud"""
        if len(historical_data) < self.senkou_b_period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        current_price = current_bar['close']
        
        ichimoku_data = self.calculate_ichimoku(highs, lows, closes)
        if ichimoku_data[0] is None:
            return 'HOLD'
        
        tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span = ichimoku_data
        
        # Determine cloud top and bottom
        cloud_top = max(senkou_span_a, senkou_span_b)
        cloud_bottom = min(senkou_span_a, senkou_span_b)
        
        # Bullish conditions:
        # 1. Price above cloud
        # 2. Tenkan-sen above Kijun-sen
        # 3. Chikou span above price 26 periods ago
        bullish = (current_price > cloud_top and 
                  tenkan_sen > kijun_sen)
        
        # Bearish conditions:
        # 1. Price below cloud
        # 2. Tenkan-sen below Kijun-sen
        bearish = (current_price < cloud_bottom and 
                  tenkan_sen < kijun_sen)
        
        # Generate signals
        if bullish:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        elif bearish:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'