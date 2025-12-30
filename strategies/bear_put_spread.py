"""
Bear Put Spread Options Strategy

A bearish options strategy that profits from a moderate decline in the underlying asset.

Strategy Structure:
- BUY Put at higher strike (ITM/ATM) - Pay premium
- SELL Put at lower strike (OTM) - Receive premium

Risk/Reward Profile:
- Net Cost (Debit): Premium paid - Premium received
- Max Profit: Strike width - Net cost
- Max Loss: Net cost (limited to debit paid)
- Break-Even: Higher strike - Net cost

Example:
- Buy $100 Put for $4.00
- Sell $90 Put for $1.50
- Net Cost: $2.50 ($250 total risk)
- Max Profit: ($100 - $90) - $2.50 = $7.50 ($750)
- Break-Even: $100 - $2.50 = $97.50

Entry Conditions:
1. Designated entry day (e.g., Monday for weekly spreads)
2. Negative momentum (bearish bias)
3. Adequate volatility for premium capture
4. No existing position

Exit Conditions:
1. Hold period expired (e.g., 7 days for weekly options)
2. Profit target reached (e.g., 50% of max profit)
3. Stop loss hit (e.g., 75% of max loss)

Author: Trading Backtest System
Date: 2024
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class Strategy:
    """Bear Put Spread Options Strategy"""
    
    def __init__(self, 
                 entry_day=0,  # Monday
                 hold_days=7,  # Weekly option duration
                 profit_target_pct=0.50,  # Exit at 50% gain
                 stop_loss_pct=0.75,  # Exit at 75% loss
                 strike_spacing=10000,  # 100 points in paise (100 * 100)
                 momentum_threshold=-0.0005,  # Negative for bearish
                 volatility_threshold=0.5,
                 atr_period=14,
                 momentum_lookback=20,
                 lot_size=75):  # NIFTY lot size:
        """
        Initialize Bear Put Spread strategy
        
        Args:
            entry_day: Day of week to enter (0=Monday, 4=Friday)
            hold_days: Days to hold position before forced exit
            profit_target_pct: Exit when P&L reaches this % of entry cost
            stop_loss_pct: Exit when loss reaches this % of entry cost
            strike_spacing: Distance between strikes in paise
            momentum_threshold: Negative momentum threshold (bearish bias)
            volatility_threshold: Minimum volatility ratio for entry
            atr_period: Period for ATR calculation
            momentum_lookback: Bars to look back for momentum
        """
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.strike_spacing = strike_spacing
        self.strike_step = strike_spacing  # Alias for compatibility
        self.momentum_threshold = momentum_threshold
        self.volatility_threshold = volatility_threshold
        self.atr_period = atr_period
        self.momentum_lookback = momentum_lookback
        self.lot_size = lot_size
        
        # Position tracking
        self.position = None
        self.entry_price = None  # Net debit paid
        self.entry_date = None
        self.entry_spot = None
        self.options_legs = []  # List of option legs in the spread
        self.max_profit = 0
        self.max_loss = 0
        
        # Trade tracking
        self.position_id = 0
        self.trade_log = []
    
    def calculate_atr(self, historical_data):
        """Calculate Average True Range"""
        if len(historical_data) < self.atr_period + 1:
            return None
        
        high = historical_data['high'].values[-self.atr_period-1:]
        low = historical_data['low'].values[-self.atr_period-1:]
        close = historical_data['close'].values[-self.atr_period-1:]
        
        if len(high) < self.atr_period + 1:
            return None
        
        # Calculate True Range
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = np.mean(true_range)
        
        return atr
    
    def calculate_volatility_ratio(self, historical_data):
        """Calculate volatility ratio (current vs average)"""
        if len(historical_data) < self.atr_period * 3:
            return None
        
        # Recent ATR
        current_atr = self.calculate_atr(historical_data)
        if current_atr is None:
            return None
        
        # Historical ATR (longer period)
        historical_window = historical_data.iloc[:-self.atr_period]
        if len(historical_window) < self.atr_period + 1:
            return None
        
        avg_atr = self.calculate_atr(historical_window)
        if avg_atr is None or avg_atr == 0:
            return None
        
        return current_atr / avg_atr
    
    def calculate_momentum(self, historical_data):
        """Calculate recent momentum to confirm bearish bias"""
        if len(historical_data) < self.momentum_lookback + 1:
            return 0
        
        closes = historical_data['close'].values
        if len(closes) < self.momentum_lookback:
            return 0
        
        recent_price = closes[-1]
        past_price = closes[-self.momentum_lookback]
        
        if past_price == 0:
            return 0
        
        momentum = (recent_price - past_price) / past_price
        return momentum
    
    def is_market_hours(self, date_val):
        """Check if during market hours (for intraday data)"""
        if isinstance(date_val, str):
            date_obj = pd.to_datetime(date_val)
        else:
            date_obj = pd.Timestamp(date_val)
        
        # Allow entry anytime during market hours
        return True
    
    def round_to_strike(self, price):
        """Round price to nearest strike"""
        return int(round(price / self.strike_step) * self.strike_step)
    
    def estimate_option_premium(self, spot, strike, atr, option_type, days_to_expiry):
        """
        Estimate option premium based on ATR and moneyness
        This is a simplified Black-Scholes approximation for simulation
        """
        # Base premium from ATR (volatility proxy)
        base_premium = atr * np.sqrt(days_to_expiry / 5.0)
        
        # Intrinsic value
        if option_type == 'CE':
            intrinsic = max(0, spot - strike)
        else:  # PE
            intrinsic = max(0, strike - spot)
        
        # Time value based on moneyness
        moneyness = abs(spot - strike) / spot
        time_value = base_premium * np.exp(-moneyness * 2)
        
        premium = intrinsic + time_value
        return max(premium, 1.0)  # Minimum premium
    
    def build_bear_put_spread(self, spot, atr, days_to_expiry):
        """
        Build bear put spread position
        
        Structure:
        - BUY put at higher strike (ITM/ATM) - Pay premium
        - SELL put at lower strike (OTM) - Receive premium
        
        Returns:
            legs: List of option legs with details
            net_debit: Net cost of the spread (negative because we pay)
            max_profit: Maximum profit potential
            max_loss: Maximum loss (limited to net debit)
        """
        # Determine strikes
        spot_rounded = self.round_to_strike(spot)
        
        # Higher strike (buy) - should be ATM or slightly OTM
        # For bearish position, we want to profit from decline
        higher_strike = spot_rounded
        
        # Ensure higher strike is at or above spot (not ITM)
        if higher_strike < spot:
            higher_strike = higher_strike + self.strike_spacing
        
        # Lower strike (sell) - OTM below spot
        lower_strike = higher_strike - self.strike_spacing
        
        # Estimate premiums
        buy_put_premium = self.estimate_option_premium(
            spot, higher_strike, atr, 'PE', days_to_expiry
        )
        
        sell_put_premium = self.estimate_option_premium(
            spot, lower_strike, atr, 'PE', days_to_expiry
        )
        
        # Build legs (NIFTY lot size configurable)
        lot_size = self.lot_size
        legs = [
            {
                'strike': higher_strike,
                'type': 'PE',
                'side': 'BUY',
                'entry_premium': buy_put_premium,
                'quantity': lot_size
            },
            {
                'strike': lower_strike,
                'type': 'PE',
                'side': 'SELL',
                'entry_premium': sell_put_premium,
                'quantity': lot_size
            }
        ]
        
        # Net debit = (Premium paid - Premium received) * lot_size
        net_debit_per_lot = buy_put_premium - sell_put_premium
        net_debit = net_debit_per_lot * lot_size
        
        # Calculate max profit and max loss (per lot basis * lot_size)
        max_profit = ((higher_strike - lower_strike) - net_debit_per_lot) * lot_size
        max_loss = net_debit
        
        return legs, -net_debit, max_profit, max_loss  # Negative because we pay
    
    def calculate_position_value(self, legs, current_spot, current_atr, days_remaining):
        """
        Calculate current value of bear put spread
        
        For a bear put spread:
        - Long put value increases as spot drops
        - Short put value also increases (liability)
        - Net value is the difference
        """
        total_value = 0
        
        for leg in legs:
            current_premium = self.estimate_option_premium(
                current_spot, leg['strike'], current_atr, leg['type'], days_remaining
            )
            
            # Multiply by quantity (lot size)
            if leg['side'] == 'BUY':
                total_value += current_premium * leg['quantity']
            else:  # SELL
                total_value -= current_premium * leg['quantity']
        
        return total_value
    
    def get_weekday(self, date_val):
        """Get day of week (0=Monday, 6=Sunday)"""
        if isinstance(date_val, str):
            date_obj = pd.to_datetime(date_val)
        else:
            date_obj = pd.Timestamp(date_val)
        return date_obj.weekday()
    
    def days_since_entry(self, current_date):
        """Calculate days since entry"""
        if self.entry_date is None:
            return 0
        
        current = pd.to_datetime(current_date)
        entry = pd.to_datetime(self.entry_date)
        return (current - entry).days
    
    def format_position_info(self):
        """Format position information for display"""
        if not self.options_legs:
            return ""
        
        info = f"\n{'='*70}\n"
        info += f"Bear Put Spread | Position ID: {self.position_id}\n"
        info += f"Entry Date: {self.entry_date} | Spot: {self.entry_spot:.2f}\n"
        info += f"Net Debit Paid: {abs(self.entry_price):.2f}\n"
        info += f"Max Profit: {self.max_profit:.2f} | Max Loss: {self.max_loss:.2f}\n"
        info += f"{'='*70}\n"
        info += f"{'Strike':<10} {'Type':<6} {'Side':<6} {'Premium':<12} {'Qty':<6}\n"
        info += f"{'-'*70}\n"
        
        for leg in self.options_legs:
            info += f"{leg['strike']:<10} {leg['type']:<6} {leg['side']:<6} {leg['entry_premium']:<12.2f} {leg['quantity']:<6}\n"
        
        info += f"{'='*70}\n"
        return info
    
    def generate_signal(self, current_bar, historical_data):
        """
        Generate trading signal for bear put spread
        
        Entry Conditions:
        1. Designated entry day (e.g., Monday)
        2. Negative momentum (bearish bias)
        3. Adequate volatility
        4. No existing position
        
        Exit Conditions:
        1. Hold period expired
        2. Profit target reached
        3. Stop loss hit
        """
        current_price = current_bar['close']
        current_date = current_bar['date']
        weekday = self.get_weekday(current_date)
        
        # Need sufficient data
        if len(historical_data) < 100:
            return 'HOLD'
        
        # Calculate indicators
        vol_ratio = self.calculate_volatility_ratio(historical_data)
        current_atr = self.calculate_atr(historical_data)
        momentum = self.calculate_momentum(historical_data)
        
        # Allow trading even if vol_ratio is None (early in dataset)
        if current_atr is None:
            return 'HOLD'
        
        # === ENTRY LOGIC ===
        if self.position is None:
            # Check entry conditions
            is_entry_day = (weekday == self.entry_day)
            is_bearish = momentum <= self.momentum_threshold  # Negative momentum
            has_volatility = (vol_ratio is None) or (vol_ratio >= self.volatility_threshold)
            is_entry_time = self.is_market_hours(current_date)
            
            if is_entry_day and is_bearish and has_volatility and is_entry_time:
                # Build bear put spread
                days_to_expiry = self.hold_days
                legs, net_cost, max_prof, max_ls = self.build_bear_put_spread(
                    current_price, current_atr, days_to_expiry
                )
                
                # Minimum entry cost check (avoid spreads that are too cheap)
                # Very cheap spreads indicate low probability of profit
                min_entry_cost = self.strike_spacing * self.lot_size * 0.001  # At least 0.1% of max spread value
                if abs(net_cost) < min_entry_cost:
                    return 'HOLD'  # Skip this entry
                
                # Enter position
                self.position = 'LONG'
                self.entry_price = net_cost  # Store as cost
                self.entry_date = current_date
                self.entry_spot = current_price
                self.options_legs = legs
                self.max_profit = max_prof
                self.max_loss = max_ls
                self.position_id += 1
                
                # Log trade entry
                self.trade_log.append({
                    'position_id': self.position_id,
                    'entry_date': current_date,
                    'entry_spot': current_price,
                    'legs': legs,
                    'net_debit': abs(net_cost),
                    'max_profit': max_prof,
                    'max_loss': max_ls,
                    'exit_date': None,
                    'exit_reason': None,
                    'pnl': None
                })
                
                # Return signal to open position
                return 'BUY'  # Signal to open position
        
        # === EXIT LOGIC ===
        elif self.position == 'LONG':
            days_held = self.days_since_entry(current_date)
            days_remaining = max(1, self.hold_days - days_held)
            
            # Calculate current position value
            current_value = self.calculate_position_value(
                self.options_legs, current_price, current_atr, days_remaining
            )
            
            # P&L calculation
            # Entry: We paid net_debit (negative entry_price)
            # Current: Position is worth current_value
            # P&L = current_value - abs(entry_price)
            pnl = current_value - abs(self.entry_price)
            pnl_pct = (pnl / abs(self.entry_price)) if abs(self.entry_price) > 0 else 0
            
            # Exit conditions
            exit_signal = False
            exit_reason = ""
            
            # 1. Time-based exit
            if days_held >= self.hold_days:
                exit_signal = True
                exit_reason = "Time expired"
            
            # 2. Profit target
            elif pnl_pct >= self.profit_target_pct:
                exit_signal = True
                exit_reason = "Profit target"
            
            # 3. Stop loss
            elif pnl_pct <= -self.stop_loss_pct:
                exit_signal = True
                exit_reason = "Stop loss"
            
            if exit_signal:
                # Update trade log
                if self.trade_log:
                    self.trade_log[-1]['exit_date'] = current_date
                    self.trade_log[-1]['exit_spot'] = current_price
                    self.trade_log[-1]['exit_reason'] = exit_reason
                    self.trade_log[-1]['pnl'] = pnl
                    self.trade_log[-1]['pnl_pct'] = pnl_pct
                
                # Clear position
                self.position = None
                self.entry_price = None
                self.entry_date = None
                self.entry_spot = None
                self.options_legs = []
                
                return 'SELL'  # Signal to close position
        
        return 'HOLD'
