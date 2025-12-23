"""
Historical Volatility Breakout Strategy

This strategy measures historical volatility and trades breakouts
when current price movements exceed normal volatility ranges.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Historical Volatility Breakout Strategy
    
    Parameters:
        vol_period: Period for volatility calculation (default: 20)
        breakout_threshold: Volatility threshold for breakouts (default: 2.0)
        lookback_period: Period for price range calculation (default: 10)
    """
    
    def __init__(self, vol_period=20, breakout_threshold=2.0, lookback_period=10, enable_short=True):
        self.vol_period = vol_period
        self.breakout_threshold = breakout_threshold
        self.lookback_period = lookback_period
        self.enable_short = enable_short
        self.position = None
    
    def calculate_historical_volatility(self, closes):
        """Calculate historical volatility"""
        if len(closes) < self.vol_period + 1:
            return None
        
        # Calculate log returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                ret = np.log(closes[i] / closes[i-1])
                returns.append(ret)
        
        if len(returns) < self.vol_period:
            return None
        
        recent_returns = returns[-self.vol_period:]
        volatility = np.std(recent_returns)
        
        return volatility
    
    def calculate_expected_range(self, closes, volatility):
        """Calculate expected price range based on volatility"""
        if volatility is None or len(closes) == 0:
            return None, None
        
        current_price = closes[-1]
        expected_move = current_price * volatility * self.breakout_threshold
        
        upper_range = current_price + expected_move
        lower_range = current_price - expected_move
        
        return upper_range, lower_range
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on volatility breakouts"""
        if len(historical_data) < self.vol_period + 1:
            return 'HOLD'
        
        closes = historical_data['close'].values
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Calculate historical volatility
        volatility = self.calculate_historical_volatility(closes)
        
        if volatility is None:
            return 'HOLD'
        
        # Calculate expected range from yesterday's close
        if len(closes) >= 2:
            yesterday_close = closes[-1]
            expected_upper, expected_lower = self.calculate_expected_range([yesterday_close], volatility)
            
            if expected_upper is None or expected_lower is None:
                return 'HOLD'
            
            # Check for volatility breakouts
            
            # Upward volatility breakout
            if current_high > expected_upper:
                if self.position == 'SHORT':
                    # Close short position
                    self.position = None
                    return 'BUY_SHORT'
                elif self.position != 'LONG':
                    # Open long position
                    self.position = 'LONG'
                    return 'BUY_LONG'
            
            # Downward volatility breakout
            elif current_low < expected_lower:
                if self.position == 'LONG':
                    # Close long position
                    self.position = None
                    return 'SELL_LONG'
                elif self.position != 'SHORT' and self.enable_short:
                    # Open short position
                    self.position = 'SHORT'
                    return 'SELL_SHORT'
            
            # Exit if price returns within normal range
            elif self.position == 'LONG' and expected_lower <= current_close <= expected_upper:
                # Price returned to normal range
                pass  # Hold position for now
            elif self.position == 'SHORT' and expected_lower <= current_close <= expected_upper:
                # Price returned to normal range
                pass  # Hold position for now
        
        return 'HOLD'