"""
Volatility Channel Strategy

This strategy creates dynamic channels based on volatility and trades
breakouts and reversals within these channels.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Volatility Channel Strategy
    
    Parameters:
        channel_period: Period for channel calculation (default: 20)
        volatility_multiplier: Multiplier for volatility bands (default: 2.0)
        breakout_mode: Trade breakouts (True) or reversals (False) (default: True)
    """
    
    def __init__(self, channel_period=20, volatility_multiplier=2.0, breakout_mode=True, enable_short=True):
        self.channel_period = channel_period
        self.volatility_multiplier = volatility_multiplier
        self.breakout_mode = breakout_mode
        self.enable_short = enable_short
        self.position = None
    
    def calculate_volatility_channels(self, closes):
        """Calculate volatility-based channels"""
        if len(closes) < self.channel_period:
            return None, None, None
        
        recent_closes = closes[-self.channel_period:]
        
        # Calculate middle line (SMA)
        middle_line = np.mean(recent_closes)
        
        # Calculate volatility (standard deviation)
        volatility = np.std(recent_closes)
        
        # Calculate upper and lower channels
        upper_channel = middle_line + (self.volatility_multiplier * volatility)
        lower_channel = middle_line - (self.volatility_multiplier * volatility)
        
        return upper_channel, middle_line, lower_channel
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on volatility channels"""
        if len(historical_data) < self.channel_period:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_close = current_bar['close']
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        # Calculate volatility channels
        channels = self.calculate_volatility_channels(closes)
        if channels[0] is None:
            return 'HOLD'
        
        upper_channel, middle_line, lower_channel = channels
        
        if self.breakout_mode:
            # Breakout strategy
            
            # Buy: Price breaks above upper channel
            if current_high > upper_channel:
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    return 'BUY_LONG'
            
            # Sell: Price breaks below lower channel
            elif current_low < lower_channel:
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    return 'SELL_SHORT'
            
            # Exit: Price returns to middle line
            elif self.position == 'LONG' and current_close <= middle_line:
                self.position = None
                return 'SELL_LONG'
            elif self.position == 'SHORT' and current_close >= middle_line:
                self.position = None
                return 'BUY_SHORT'
        
        else:
            # Mean reversion strategy
            
            # Buy: Price touches lower channel (oversold)
            if current_low <= lower_channel:
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    return 'BUY_LONG'
            
            # Sell: Price touches upper channel (overbought)
            elif current_high >= upper_channel:
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    return 'SELL_SHORT'
            
            # Exit: Price returns to middle line
            elif self.position == 'LONG' and current_close >= middle_line:
                self.position = None
                return 'SELL_LONG'
            elif self.position == 'SHORT' and current_close <= middle_line:
                self.position = None
                return 'BUY_SHORT'
        
        return 'HOLD'