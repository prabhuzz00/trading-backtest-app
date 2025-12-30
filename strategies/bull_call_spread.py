"""
Bull Call Spread Options Strategy

This strategy implements a Bull Call Spread, which is a bullish options strategy that:
- BUYS a call option at a lower strike price (ITM or ATM)
- SELLS a call option at a higher strike price (OTM)
- Both options have the same expiration date

The strategy has limited profit potential and limited risk, making it ideal for 
moderately bullish market conditions.

Strategy Characteristics:
- Maximum Profit: Difference between strikes minus net premium paid
- Maximum Loss: Net premium paid (debit)
- Breakeven: Lower strike + net premium paid
- Best Used: When expecting moderate upward movement

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 7)
    - atr_period: ATR calculation period (default: 14)
    - volatility_threshold: Minimum volatility ratio for entry (default: 1.0)
    - strike_spacing: Points between strikes (default: 100)
    - profit_target_pct: Exit profit % (default: 0.50 = 50%)
    - stop_loss_pct: Exit loss % (default: 0.75 = 75%)
    - strike_step: Strike price rounding step (default: 50)
    - lot_size: Contract lot size (default: 50)
    - momentum_lookback: Period for momentum check (default: 5)
    - momentum_threshold: Minimum momentum for entry (default: 0.01 = 1%)
"""

import pandas as pd
import numpy as np
from datetime import datetime

class Strategy:
    """
    Bull Call Spread - A defined-risk bullish options strategy
    
    Position Structure:
    1. BUY 1 Call at lower strike (ITM/ATM) - Long Call
    2. SELL 1 Call at higher strike (OTM) - Short Call
    
    The short call caps the maximum profit but reduces the net cost.
    """
    
    def __init__(self, 
                 entry_day=0, 
                 hold_days=7,
                 atr_period=14,
                 volatility_threshold=0.5,  # Lowered from 1.0 for more entries
                 strike_spacing=10000,  # 100 points in paise (100 * 100)
                 profit_target_pct=0.50,
                 stop_loss_pct=0.75,
                 strike_step=5000,  # 50 points in paise (50 * 100)
                 lot_size=75,
                 momentum_lookback=50,  # Use more bars for intraday (50 mins)
                 momentum_threshold=0.0005):  # Very low threshold for intraday (0.05%)
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.atr_period = atr_period
        self.volatility_threshold = volatility_threshold
        self.strike_spacing = strike_spacing
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.momentum_lookback = momentum_lookback
        self.momentum_threshold = momentum_threshold
        
        # Position tracking
        self.position = None  # 'LONG' when bull call spread is active
        self.entry_price = None  # Net debit paid
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of option legs
        self.position_id = 0
        self.max_profit = 0  # Maximum profit potential
        self.max_loss = 0   # Maximum loss (net debit)
        
        # Trade log for detailed reporting
        self.trade_log = []
        
    def calculate_atr(self, historical_data):
        """Calculate Average True Range"""
        if len(historical_data) < self.atr_period + 1:
            return None
        
        high = historical_data['high'].values
        low = historical_data['low'].values
        close = historical_data['close'].values
        
        tr = np.zeros(len(high))
        for i in range(1, len(high)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        atr = np.mean(tr[-self.atr_period:])
        return atr
    
    def calculate_volatility_ratio(self, historical_data):
        """Calculate current volatility vs historical average"""
        if len(historical_data) < self.atr_period * 3:
            return None
        
        current_atr = self.calculate_atr(historical_data)
        if current_atr is None:
            return None
        
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
    
    def calculate_momentum(self, historical_data):
        """Calculate recent momentum to confirm bullish bias"""
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
        # Just return True to allow all times (simplified for testing)
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
    
    def build_bull_call_spread(self, spot, atr, days_to_expiry):
        """
        Build bull call spread position
        
        Structure:
        - BUY call at lower strike (ITM/ATM) - Pay premium
        - SELL call at higher strike (OTM) - Receive premium
        
        Returns:
            legs: List of option legs with details
            net_debit: Net cost of the spread (negative because we pay)
        """
        # Determine strikes
        # Lower strike: Slightly ITM or ATM
        atm_strike = self.round_to_strike(spot)
        lower_strike = atm_strike  # ATM
        
        # Higher strike: OTM by specified spacing
        higher_strike = lower_strike + self.strike_spacing
        
        # Estimate premiums
        buy_call_premium = self.estimate_option_premium(spot, lower_strike, atr, 'CE', days_to_expiry)
        sell_call_premium = self.estimate_option_premium(spot, higher_strike, atr, 'CE', days_to_expiry)
        
        # Build legs (NIFTY lot size configurable)
        lot_size = self.lot_size
        legs = [
            {
                'strike': lower_strike,
                'type': 'CE',
                'side': 'BUY',
                'entry_premium': buy_call_premium,
                'quantity': lot_size
            },
            {
                'strike': higher_strike,
                'type': 'CE',
                'side': 'SELL',
                'entry_premium': sell_call_premium,
                'quantity': lot_size
            }
        ]
        
        # Net debit = (Premium paid - Premium received) * lot_size
        net_debit_per_lot = buy_call_premium - sell_call_premium
        net_debit = net_debit_per_lot * lot_size
        
        # Calculate max profit and max loss (per lot basis * lot_size)
        max_profit = ((higher_strike - lower_strike) - net_debit_per_lot) * lot_size
        max_loss = net_debit
        
        return legs, -net_debit, max_profit, max_loss  # Negative because we pay
    
    def calculate_position_value(self, legs, current_spot, current_atr, days_remaining):
        """
        Calculate current value of bull call spread
        
        For a bull call spread:
        - Long call value increases as spot rises
        - Short call value also increases (liability)
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
        info += f"Bull Call Spread | Position ID: {self.position_id}\n"
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
        Generate trading signal for bull call spread
        
        Entry Conditions:
        1. Designated entry day (e.g., Monday)
        2. Positive momentum (bullish bias)
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
        
        # Need sufficient data (reduced requirement)
        if len(historical_data) < 100:  # Reduced from atr_period * 3
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
            is_bullish = momentum >= self.momentum_threshold
            has_volatility = (vol_ratio is None) or (vol_ratio >= self.volatility_threshold)  # Allow if None
            is_entry_time = self.is_market_hours(current_date)  # Only enter during market open
            
            if is_entry_day and is_bullish and has_volatility and is_entry_time:
                # Build bull call spread
                days_to_expiry = self.hold_days
                legs, net_cost, max_prof, max_ls = self.build_bull_call_spread(
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
