"""
Money Flow Index (MFI) Strategy

This strategy uses Money Flow Index which combines price and volume
to measure buying and selling pressure (volume-weighted RSI).
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Money Flow Index Strategy
    
    Parameters:
        mfi_period: MFI calculation period (default: 14)
        overbought_level: MFI overbought threshold (default: 80)
        oversold_level: MFI oversold threshold (default: 20)
    """
    
    def __init__(self, mfi_period=14, overbought_level=80, oversold_level=20, enable_short=True):
        self.mfi_period = mfi_period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.enable_short = enable_short
        self.position = None
    
    def calculate_typical_price(self, high, low, close):
        """Calculate Typical Price"""
        return (high + low + close) / 3
    
    def calculate_money_flow(self, typical_price, volume):
        """Calculate Raw Money Flow"""
        return typical_price * volume
    
    def calculate_mfi(self, highs, lows, closes, volumes):
        """Calculate Money Flow Index"""
        if len(closes) < self.mfi_period + 1:
            return None
        
        typical_prices = []
        money_flows = []
        
        for i in range(len(closes)):
            tp = self.calculate_typical_price(highs[i], lows[i], closes[i])
            typical_prices.append(tp)
            
            # Use default volume if not provided
            volume = volumes[i] if i < len(volumes) else 1000
            mf = self.calculate_money_flow(tp, volume)
            money_flows.append(mf)
        
        # Calculate positive and negative money flows
        positive_mf = 0
        negative_mf = 0
        
        for i in range(len(typical_prices) - self.mfi_period, len(typical_prices)):
            if i == 0:
                continue
                
            if typical_prices[i] > typical_prices[i-1]:
                positive_mf += money_flows[i]
            elif typical_prices[i] < typical_prices[i-1]:
                negative_mf += money_flows[i]
        
        # Calculate Money Flow Ratio and MFI
        if negative_mf == 0:
            return 100
        
        money_ratio = positive_mf / negative_mf
        mfi = 100 - (100 / (1 + money_ratio))
        
        return mfi
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on MFI levels"""
        if len(historical_data) < self.mfi_period + 1:
            return 'HOLD'
        
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        # Use volume if available, otherwise use default values
        if 'volume' in historical_data.columns:
            volumes = historical_data['volume'].values
        else:
            volumes = [1000] * len(closes)
        
        # Include current bar
        current_highs = np.append(highs, current_bar['high'])
        current_lows = np.append(lows, current_bar['low'])
        current_closes = np.append(closes, current_bar['close'])
        current_volumes = np.append(volumes, current_bar.get('volume', 1000))
        
        mfi = self.calculate_mfi(current_highs, current_lows, current_closes, current_volumes)
        
        if mfi is None:
            return 'HOLD'
        
        # Momentum-based signals
        
        # Buy: MFI oversold (strong selling pressure ending)
        if mfi <= self.oversold_level:
            if self.position == 'SHORT':
                # Close short position
                self.position = None
                return 'BUY_SHORT'
            elif self.position != 'LONG':
                # Open long position
                self.position = 'LONG'
                return 'BUY_LONG'
        
        # Sell: MFI overbought (strong buying pressure ending)
        elif mfi >= self.overbought_level:
            if self.position == 'LONG':
                # Close long position
                self.position = None
                return 'SELL_LONG'
            elif self.position != 'SHORT' and self.enable_short:
                # Open short position
                self.position = 'SHORT'
                return 'SELL_SHORT'
        
        return 'HOLD'