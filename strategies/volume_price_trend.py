"""
Volume-Price Trend (VPT) Strategy

This strategy uses Volume-Price Trend indicator which combines price
and volume to identify momentum. Rising VPT suggests accumulation.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Volume-Price Trend Strategy
    
    Parameters:
        vpt_ma_period: VPT moving average period (default: 20)
        signal_threshold: Minimum VPT change for signal (default: 1000)
    """
    
    def __init__(self, vpt_ma_period=20, signal_threshold=1000, enable_short=True):
        self.vpt_ma_period = vpt_ma_period
        self.signal_threshold = signal_threshold
        self.enable_short = enable_short
        self.position = None
        self.previous_vpt = 0
        self.vpt_values = []
    
    def calculate_vpt(self, current_bar, previous_close):
        """Calculate Volume-Price Trend"""
        if previous_close == 0:
            return self.previous_vpt
        
        price_change_pct = (current_bar['close'] - previous_close) / previous_close
        volume = current_bar.get('volume', 1000)  # Default volume if not available
        
        vpt = self.previous_vpt + (price_change_pct * volume)
        self.previous_vpt = vpt
        
        return vpt
    
    def calculate_vpt_ma(self):
        """Calculate VPT moving average"""
        if len(self.vpt_values) < self.vpt_ma_period:
            return None
        
        return np.mean(self.vpt_values[-self.vpt_ma_period:])
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on VPT momentum"""
        if len(historical_data) < 2:
            return 'HOLD'
        
        # Get previous close
        previous_close = historical_data['close'].iloc[-2]
        
        # Calculate current VPT
        current_vpt = self.calculate_vpt(current_bar, previous_close)
        self.vpt_values.append(current_vpt)
        
        # Keep only necessary history
        if len(self.vpt_values) > self.vpt_ma_period * 2:
            self.vpt_values = self.vpt_values[-self.vpt_ma_period * 2:]
        
        # Calculate VPT moving average
        vpt_ma = self.calculate_vpt_ma()
        
        if vpt_ma is None or len(self.vpt_values) < 2:
            return 'HOLD'
        
        # Calculate VPT momentum
        vpt_change = current_vpt - self.vpt_values[-2] if len(self.vpt_values) >= 2 else 0
        
        # Generate signals
        
        # Buy: VPT above MA and strong positive momentum
        if current_vpt > vpt_ma and vpt_change > self.signal_threshold:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: VPT below MA and strong negative momentum
        elif current_vpt < vpt_ma and vpt_change < -self.signal_threshold:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        # Exit on reversal
        elif self.position == 'LONG' and current_vpt < vpt_ma:
            self.position = None
            return 'SELL_LONG'
        
        elif self.position == 'SHORT' and current_vpt > vpt_ma:
            self.position = None
            return 'BUY_SHORT'
        
        return 'HOLD'