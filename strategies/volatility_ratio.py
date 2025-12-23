"""
Volatility Ratio Strategy

This strategy compares short-term volatility to long-term volatility
to identify periods of expansion or contraction in market volatility.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Volatility Ratio Strategy
    
    Parameters:
        short_vol_period: Short-term volatility period (default: 10)
        long_vol_period: Long-term volatility period (default: 30)
        expansion_threshold: Threshold for volatility expansion (default: 1.5)
        contraction_threshold: Threshold for volatility contraction (default: 0.7)
    """
    
    def __init__(self, short_vol_period=10, long_vol_period=30, 
                 expansion_threshold=1.5, contraction_threshold=0.7, enable_short=True):
        self.short_vol_period = short_vol_period
        self.long_vol_period = long_vol_period
        self.expansion_threshold = expansion_threshold
        self.contraction_threshold = contraction_threshold
        self.enable_short = enable_short
        self.position = None
    
    def calculate_volatility(self, closes, period):
        """Calculate volatility for given period"""
        if len(closes) < period + 1:
            return None
        
        # Calculate returns
        returns = []
        for i in range(len(closes) - period, len(closes)):
            if i > 0 and closes[i-1] != 0:
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(ret)
        
        if len(returns) < period - 1:
            return None
        
        volatility = np.std(returns)
        return volatility
    
    def calculate_volatility_ratio(self, closes):
        """Calculate ratio of short-term to long-term volatility"""
        short_vol = self.calculate_volatility(closes, self.short_vol_period)
        long_vol = self.calculate_volatility(closes, self.long_vol_period)
        
        if short_vol is None or long_vol is None or long_vol == 0:
            return None
        
        vol_ratio = short_vol / long_vol
        return vol_ratio
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on volatility ratio"""
        if len(historical_data) < self.long_vol_period + 1:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        
        # Calculate volatility ratio
        vol_ratio = self.calculate_volatility_ratio(closes)
        
        if vol_ratio is None:
            return 'HOLD'
        
        # Calculate momentum for trend direction
        if len(closes) >= 5:
            momentum = (current_close - closes[-5]) / closes[-5] * 100
        else:
            momentum = 0
        
        # Trading logic based on volatility regime
        
        # Volatility expansion: Follow momentum
        if vol_ratio >= self.expansion_threshold:
            if momentum > 1.0:  # Positive momentum during vol expansion
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    return 'BUY_LONG'
            elif momentum < -1.0:  # Negative momentum during vol expansion
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    return 'SELL_SHORT'
        
        # Volatility contraction: Mean reversion
        elif vol_ratio <= self.contraction_threshold:
            # Calculate mean reversion signal
            if len(closes) >= 20:
                mean_price = np.mean(closes[-20:])
                price_deviation = (current_close - mean_price) / mean_price * 100
                
                # Buy on oversold during low volatility
                if price_deviation <= -2.0:
                    if self.position == 'SHORT':
                        # Close short position
                        self.position = None
                        return 'BUY_SHORT'
                    elif self.position != 'LONG':
                        # Open long position
                        self.position = 'LONG'
                        return 'BUY_LONG'
                
                # Sell on overbought during low volatility
                elif price_deviation >= 2.0:
                    if self.position == 'LONG':
                        # Close long position
                        self.position = None
                        return 'SELL_LONG'
                    elif self.position != 'SHORT' and self.enable_short:
                        # Open short position
                        self.position = 'SHORT'
                        return 'SELL_SHORT'
        
        return 'HOLD'