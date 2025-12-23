"""
Contrarian Strategy

This strategy goes against the prevailing market sentiment. It buys during
market declines and sells during market rallies, assuming temporary overreactions.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Contrarian Strategy
    
    Parameters:
        lookback_period: Period to analyze price movement (default: 10)
        decline_threshold: Minimum decline % to trigger buy (default: -3.0)
        rally_threshold: Minimum rally % to trigger sell (default: 3.0)
    """
    
    def __init__(self, lookback_period=10, decline_threshold=-3.0, rally_threshold=3.0, enable_short=True):
        self.lookback_period = lookback_period
        self.decline_threshold = decline_threshold
        self.rally_threshold = rally_threshold
        self.enable_short = enable_short
        self.position = None
    
    def calculate_price_change_percent(self, current_price, historical_prices):
        """Calculate percentage change over lookback period"""
        if len(historical_prices) < self.lookback_period:
            return 0
        
        past_price = historical_prices[-self.lookback_period]
        if past_price == 0:
            return 0
        
        return ((current_price - past_price) / past_price) * 100
    
    def generate_signal(self, current_bar, historical_data):
        """Generate contrarian trading signals"""
        if len(historical_data) < self.lookback_period + 1:
            return 'HOLD'
        
        current_price = current_bar['close']
        historical_prices = historical_data['close'].values
        
        # Calculate price change percentage
        price_change_pct = self.calculate_price_change_percent(current_price, historical_prices)
        
        # Contrarian logic: Buy on declines, sell on rallies
        
        # Buy signal on significant decline (market overreaction)
        if price_change_pct <= self.decline_threshold:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell signal on significant rally
        elif price_change_pct >= self.rally_threshold:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit on moderate reversal (take profits)
        elif self.position == 'LONG' and price_change_pct >= 0:
            # Price has recovered, take profits
            self.position = None
            return 'SELL_LONG'
        
        elif self.position == 'SHORT' and price_change_pct <= 0:
            # Price has declined from rally, take profits
            self.position = None
            return 'BUY_SHORT'
        
        return 'HOLD'