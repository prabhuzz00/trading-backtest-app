"""
Commodity Channel Index (CCI) Strategy

This strategy uses CCI to identify cyclical trends and momentum.
CCI measures the deviation of price from its statistical mean.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Commodity Channel Index Strategy
    
    Parameters:
        cci_period: CCI calculation period (default: 20)
        overbought_level: CCI overbought threshold (default: 100)
        oversold_level: CCI oversold threshold (default: -100)
    """
    
    def __init__(self, cci_period=20, overbought_level=100, oversold_level=-100, enable_short=True):
        self.cci_period = cci_period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.enable_short = enable_short
        self.position = None
    
    def calculate_typical_price(self, high, low, close):
        """Calculate Typical Price (HLC/3)"""
        return (high + low + close) / 3
    
    def calculate_cci(self, highs, lows, closes):
        """Calculate Commodity Channel Index"""
        if len(closes) < self.cci_period:
            return None
        
        # Calculate typical prices
        typical_prices = []
        for i in range(len(closes)):
            tp = self.calculate_typical_price(highs[i], lows[i], closes[i])
            typical_prices.append(tp)
        
        # Get recent typical prices
        recent_tp = typical_prices[-self.cci_period:]
        
        # Calculate Simple Moving Average of Typical Price
        sma_tp = np.mean(recent_tp)
        
        # Calculate Mean Deviation
        mean_deviation = np.mean([abs(tp - sma_tp) for tp in recent_tp])
        
        if mean_deviation == 0:
            return 0
        
        # Calculate CCI
        current_tp = typical_prices[-1]
        cci = (current_tp - sma_tp) / (0.015 * mean_deviation)
        
        return cci
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on CCI levels"""
        if len(historical_data) < self.cci_period:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        # Include current bar data
        current_highs = np.append(highs, current_bar['high'])
        current_lows = np.append(lows, current_bar['low'])
        current_closes = np.append(closes, current_bar['close'])
        
        cci = self.calculate_cci(current_highs, current_lows, current_closes)
        
        if cci is None:
            return 'HOLD'
        
        # Momentum-based signals
        
        # Buy: CCI crosses above oversold level (momentum building)
        if cci > self.oversold_level and cci < 0:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: CCI crosses below overbought level (momentum fading)
        elif cci < self.overbought_level and cci > 0:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Alternative: Sell when CCI goes extremely overbought
        elif cci >= self.overbought_level:
            if self.position == 'LONG':
                self.position = None
                return 'SELL_LONG'
        
        # Cover short when CCI goes extremely oversold
        elif cci <= self.oversold_level:
            if self.position == 'SHORT':
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'