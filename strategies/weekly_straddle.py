"""
Weekly Straddle Strategy (Volatility Expansion/Contraction)

This strategy simulates a weekly straddle approach by:
- Entering on Monday when volatility conditions are favorable
- Holding until end of week (Friday) or when profit/loss targets are hit
- Using ATR to measure volatility (proxy for option premium)
- Trading both long and short based on expected volatility moves

Parameters:
    - atr_period: Period for ATR calculation (default: 14)
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 4 for Monday-Friday)
    - volatility_threshold: Minimum ATR ratio for entry (default: 1.2)
    - profit_target: Exit at this profit % (default: 0.15 for 15%)
    - stop_loss: Exit at this loss % (default: 0.25 for 25%)
    - enable_short: Enable short straddle (credit spread) (default: False)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class Strategy:
    """
    Weekly Straddle Strategy using volatility expansion/contraction
    
    Long Straddle: Buy when expecting volatility expansion (debit strategy)
    Short Straddle: Sell when expecting volatility contraction (credit strategy)
    """
    
    def __init__(self, atr_period=14, entry_day=0, hold_days=4, 
                 volatility_threshold=1.2, profit_target=0.15, 
                 stop_loss=0.25, enable_short=False):
        self.atr_period = atr_period
        self.entry_day = entry_day  # 0=Monday, 4=Friday
        self.hold_days = hold_days
        self.volatility_threshold = volatility_threshold
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.enable_short = enable_short
        
        self.position = None  # 'LONG' or 'SHORT' or None
        self.entry_price = None
        self.entry_date = None
        self.entry_atr = None
        
    def calculate_atr(self, historical_data):
        """Calculate Average True Range"""
        if len(historical_data) < self.atr_period + 1:
            return None
        
        high = historical_data['high'].values
        low = historical_data['low'].values
        close = historical_data['close'].values
        
        # True Range calculation
        tr = np.zeros(len(high))
        for i in range(1, len(high)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        # ATR is the moving average of TR
        atr = np.mean(tr[-self.atr_period:])
        return atr
    
    def get_weekday(self, date_val):
        """Get day of week (0=Monday, 6=Sunday)"""
        if isinstance(date_val, str):
            date_obj = pd.to_datetime(date_val)
        else:
            date_obj = pd.Timestamp(date_val)
        return date_obj.weekday()
    
    def days_since_entry(self, current_date):
        """Calculate business days since entry"""
        if self.entry_date is None:
            return 0
        
        if isinstance(current_date, str):
            current = pd.to_datetime(current_date)
        else:
            current = pd.Timestamp(current_date)
            
        if isinstance(self.entry_date, str):
            entry = pd.to_datetime(self.entry_date)
        else:
            entry = pd.Timestamp(self.entry_date)
        
        return (current - entry).days
    
    def calculate_volatility_ratio(self, historical_data):
        """
        Calculate ratio of current ATR to average ATR
        High ratio = high volatility (good for long straddle)
        Low ratio = low volatility (good for short straddle)
        """
        if len(historical_data) < self.atr_period * 3:
            return None
        
        current_atr = self.calculate_atr(historical_data)
        if current_atr is None:
            return None
        
        # Calculate average ATR over longer period
        long_period_data = historical_data.tail(self.atr_period * 3)
        atr_values = []
        
        for i in range(self.atr_period, len(long_period_data)):
            window = long_period_data.iloc[max(0, i-self.atr_period):i]
            if len(window) >= self.atr_period:
                atr_val = self.calculate_atr(window)
                if atr_val is not None:
                    atr_values.append(atr_val)
        
        if not atr_values:
            return None
        
        avg_atr = np.mean(atr_values)
        if avg_atr == 0:
            return None
        
        return current_atr / avg_atr
    
    def generate_signal(self, current_bar, historical_data):
        """
        Generate trading signal based on weekly straddle logic
        
        Entry Logic:
        - Long Straddle: Enter on designated day if volatility is rising
        - Short Straddle: Enter on designated day if volatility is falling
        
        Exit Logic:
        - Hold for specified days
        - Or exit if profit target or stop loss hit
        """
        current_price = current_bar['close']
        current_date = current_bar['date']
        weekday = self.get_weekday(current_date)
        
        # Need enough data for calculations
        if len(historical_data) < self.atr_period * 3:
            return 'HOLD'
        
        # Calculate volatility metrics
        vol_ratio = self.calculate_volatility_ratio(historical_data)
        current_atr = self.calculate_atr(historical_data)
        
        if vol_ratio is None or current_atr is None:
            return 'HOLD'
        
        # Manage existing position
        if self.position is not None:
            days_held = self.days_since_entry(current_date)
            
            if self.position == 'LONG':
                # Long straddle: profit from volatility expansion
                pnl_pct = (current_price - self.entry_price) / self.entry_price
                
                # Exit conditions
                # 1. Hit profit target
                if abs(pnl_pct) >= self.profit_target:
                    self.position = None
                    self.entry_price = None
                    self.entry_date = None
                    return 'SELL_LONG'
                
                # 2. Hit stop loss
                if abs(pnl_pct) >= self.stop_loss:
                    self.position = None
                    self.entry_price = None
                    self.entry_date = None
                    return 'SELL_LONG'
                
                # 3. Held for target days (weekly expiry)
                if days_held >= self.hold_days:
                    self.position = None
                    self.entry_price = None
                    self.entry_date = None
                    return 'SELL_LONG'
            
            elif self.position == 'SHORT':
                # Short straddle: profit from volatility contraction
                pnl_pct = (self.entry_price - current_price) / self.entry_price
                
                # Exit conditions
                if abs(pnl_pct) >= self.profit_target:
                    self.position = None
                    self.entry_price = None
                    self.entry_date = None
                    return 'BUY_SHORT'
                
                if abs(pnl_pct) >= self.stop_loss:
                    self.position = None
                    self.entry_price = None
                    self.entry_date = None
                    return 'BUY_SHORT'
                
                if days_held >= self.hold_days:
                    self.position = None
                    self.entry_price = None
                    self.entry_date = None
                    return 'BUY_SHORT'
        
        # Entry logic - only enter on specified weekday
        if weekday == self.entry_day and self.position is None:
            # Long Straddle: Enter when volatility is expanding
            # (expecting continued expansion = option prices increase)
            if vol_ratio >= self.volatility_threshold:
                self.position = 'LONG'
                self.entry_price = current_price
                self.entry_date = current_date
                self.entry_atr = current_atr
                return 'BUY_LONG'
            
            # Short Straddle: Enter when volatility is contracting
            # (expecting continued contraction = option prices decrease)
            elif vol_ratio < (2.0 - self.volatility_threshold) and self.enable_short:
                self.position = 'SHORT'
                self.entry_price = current_price
                self.entry_date = current_date
                self.entry_atr = current_atr
                return 'SELL_SHORT'
        
        return 'HOLD'
