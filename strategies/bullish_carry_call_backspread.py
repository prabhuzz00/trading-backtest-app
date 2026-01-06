"""
Bullish Carry + Call Backspread Options Strategy

This strategy combines income generation with unlimited upside potential:
- SELLS near-the-money (ATM) calls to collect premium (carry/income)
- BUYS more out-of-the-money (OTM) calls (backspread structure)
- Ratio: typically 1 short : 2 long (1x2 or 1x3)
- Net credit or small debit depending on strikes

The strategy profits from:
1. Time decay if market stays flat (carry component)
2. Large upward moves (backspread component provides unlimited upside)

Strategy Characteristics:
- Maximum Profit: Unlimited above upper breakeven
- Maximum Loss: Between strikes (limited)
- Breakeven: Two levels (lower at short strike + credit, upper at calculated point)
- Best Used: In bullish markets expecting volatility
- Benefits from: Large upward moves, volatility expansion

Risk Management:
- Monitor the zone between strikes (max loss area)
- Consider early exit if price stalls between strikes
- Size position appropriately
- Use stop losses in danger zone
- Ideal when expecting strong directional move

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 10)
    - short_call_otm_pct: % above spot for short calls (default: 0.02 = 2%)
    - long_call_otm_pct: % above spot for long calls (default: 0.05 = 5%)
    - backspread_ratio: Ratio of long to short (default: 2.0)
    - max_debit_pct: Maximum net debit as % of spot (default: 0.005 = 0.5%)
    - profit_target_pct: Exit profit % (default: 2.0 = 200%)
    - stop_loss_pct: Exit loss % (default: 0.75 = 75%)
    - strike_step: Strike price rounding step (default: 50)
    - lot_size: Contract lot size (default: 75)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.db_connection import get_stock_data

class Strategy:
    """
    Bullish Carry + Call Backspread - Income plus unlimited upside
    
    Position Structure:
    1. SELL 1x ATM/near-ATM Call (income/carry)
    2. BUY 2x OTM Call (backspread for unlimited upside)
    
    Profits from theta decay at lower prices and from large upward moves.
    """
    
    def __init__(self, 
                 entry_day=None,
                 hold_days=10,
                 short_call_otm_pct=0.02,
                 long_call_otm_pct=0.05,
                 backspread_ratio=2.0,
                 max_debit_pct=0.005,
                 profit_target_pct=2.0,
                 stop_loss_pct=0.75,
                 strike_step=5000,
                 lot_size=75,
                 min_days_to_expiry=7,
                 max_days_to_expiry=30,
                 momentum_lookback=10,
                 momentum_threshold=0.01):
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.short_call_otm_pct = short_call_otm_pct
        self.long_call_otm_pct = long_call_otm_pct
        self.backspread_ratio = backspread_ratio
        self.max_debit_pct = max_debit_pct
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.momentum_lookback = momentum_lookback
        self.momentum_threshold = momentum_threshold
        
        # Position tracking
        self.position = None  # 'CARRY_BACKSPREAD' when position is active
        self.entry_cost = None  # Net debit/credit
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of all legs
        self.position_id = 0
        self.short_call_strike = None
        self.long_call_strike = None
        self.net_delta = 0
        
        # Trade log for detailed reporting
        self.trade_log = []
        
        # Underlying symbol tracking
        self.underlying_symbol = None
        self.option_expiry_date = None
        
        # IV tracking
        self.iv_history = []
        
    def calculate_atr(self, historical_data):
        """Calculate Average True Range"""
        if len(historical_data) < 15:
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
        
        atr = np.mean(tr[-14:])
        return atr
    
    def calculate_momentum(self, historical_data):
        """Calculate price momentum"""
        if len(historical_data) < self.momentum_lookback + 1:
            return 0
        
        current_price = historical_data['close'].iloc[-1]
        past_price = historical_data['close'].iloc[-self.momentum_lookback]
        
        momentum = (current_price - past_price) / past_price
        return momentum
    
    def calculate_iv_percentile(self, historical_data):
        """Calculate implied volatility percentile using historical volatility"""
        if len(historical_data) < 30:
            return 50
        
        returns = historical_data['close'].pct_change()
        current_hv = returns.tail(20).std() * np.sqrt(252)
        
        self.iv_history.append(current_hv)
        
        if len(self.iv_history) > 252:
            self.iv_history = self.iv_history[-252:]
        
        if len(self.iv_history) < 30:
            return 50
        
        percentile = (np.sum(np.array(self.iv_history) < current_hv) / len(self.iv_history)) * 100
        
        return percentile
    
    def round_to_strike(self, price):
        """Round price to nearest strike"""
        return int(round(price / self.strike_step) * self.strike_step)
    
    def set_underlying_symbol(self, symbol):
        """Set the underlying symbol"""
        self.underlying_symbol = symbol
        self.option_expiry_date = None
    
    def get_next_expiry(self, current_date):
        """Get next weekly expiry (Thursday)"""
        current_date_obj = pd.to_datetime(current_date)
        
        days_ahead = 3 - current_date_obj.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        next_expiry = current_date_obj + timedelta(days=days_ahead)
        
        days_to_expiry = (next_expiry - current_date_obj).days
        
        if days_to_expiry < self.min_days_to_expiry:
            next_expiry += timedelta(days=7)
        
        return next_expiry
    
    def get_option_symbol(self, strike, option_type, expiry_date):
        """Construct option symbol name"""
        expiry_str = expiry_date.strftime('%Y%m%d')
        strike_paise = int(strike)
        symbol = f"NSEFO:#NIFTY{expiry_str}{option_type}{strike_paise}"
        return symbol
    
    def fetch_option_premium(self, strike, option_type, current_date, expiry_date):
        """Fetch actual option premium from database"""
        try:
            symbol = self.get_option_symbol(strike, option_type, expiry_date)
            current_date_obj = pd.to_datetime(current_date)
            
            start_date = (current_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (current_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            
            df = get_stock_data(symbol, start_date, end_date, use_cache=True)
            
            if df.empty:
                return None
            
            df['date_diff'] = abs((df['date'] - current_date_obj).dt.total_seconds())
            closest_idx = df['date_diff'].idxmin()
            premium = df.loc[closest_idx, 'close']
            
            return premium
            
        except Exception as e:
            return None
    
    def estimate_premium_theoretical(self, spot, strike, atr, option_type, days_to_expiry):
        """Theoretical option premium estimation"""
        if days_to_expiry <= 0 or atr is None or atr == 0:
            return 0
        
        iv_estimate = (atr / spot) * np.sqrt(252 / days_to_expiry)
        iv_estimate = max(0.1, min(1.0, iv_estimate))
        
        time_factor = np.sqrt(days_to_expiry / 365.0)
        
        if option_type == 'CE':
            moneyness = (strike - spot) / spot
            if moneyness > 0:
                intrinsic = 0
                extrinsic = spot * iv_estimate * time_factor * np.exp(-moneyness * 2)
            else:
                intrinsic = spot - strike
                extrinsic = spot * iv_estimate * time_factor * 0.5
        else:
            moneyness = (spot - strike) / spot
            if moneyness > 0:
                intrinsic = 0
                extrinsic = spot * iv_estimate * time_factor * np.exp(-moneyness * 2)
            else:
                intrinsic = strike - spot
                extrinsic = spot * iv_estimate * time_factor * 0.5
        
        premium = intrinsic + extrinsic
        return max(0, premium)
    
    def get_premium_value(self, strike, option_type, current_date, expiry_date, spot, atr):
        """Get option premium"""
        premium = self.fetch_option_premium(strike, option_type, current_date, expiry_date)
        
        if premium is not None and premium > 0:
            return premium
        
        days_to_expiry = (pd.to_datetime(expiry_date) - pd.to_datetime(current_date)).days
        return self.estimate_premium_theoretical(spot, strike, atr, option_type, days_to_expiry)
    
    def should_enter(self, data):
        """Check if conditions are met to enter carry backspread"""
        if self.position is not None:
            return False
        
        if len(data) < max(self.momentum_lookback + 1, 30):
            return False
        
        # Check for bullish momentum
        historical_data = data.iloc[:-1]
        momentum = self.calculate_momentum(historical_data)
        
        # Require positive momentum for bullish setup
        if momentum < self.momentum_threshold:
            return False
        
        return True
    
    def build_carry_backspread(self, current_bar, historical_data):
        """Build carry + backspread position"""
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            expiry_date = self.get_next_expiry(current_date)
            self.option_expiry_date = expiry_date
            
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            legs = []
            
            # 1. SELL near-ATM calls (carry component)
            short_call_strike = self.round_to_strike(spot * (1 + self.short_call_otm_pct))
            short_call_premium = self.get_premium_value(short_call_strike, 'CE', current_date, expiry_date, spot, atr)
            
            if short_call_premium <= 0:
                return None
            
            short_call_credit = short_call_premium * self.lot_size
            
            # Estimate short call delta
            short_moneyness = (short_call_strike - spot) / spot
            short_call_delta = -max(0.3, 0.5 * np.exp(-short_moneyness * 5))
            
            legs.append({
                'type': 'SELL_CALL',
                'strike': short_call_strike,
                'premium': short_call_premium,
                'quantity': self.lot_size,
                'delta': short_call_delta,
                'label': 'SHORT_CALL_CARRY'
            })
            
            # 2. BUY OTM calls (backspread component)
            long_call_strike = self.round_to_strike(spot * (1 + self.long_call_otm_pct))
            long_call_premium = self.get_premium_value(long_call_strike, 'CE', current_date, expiry_date, spot, atr)
            
            if long_call_premium <= 0:
                return None
            
            # Calculate quantity for backspread (ratio)
            long_call_quantity = int(self.lot_size * self.backspread_ratio)
            long_call_cost = long_call_premium * long_call_quantity
            
            # Estimate long call delta
            long_moneyness = (long_call_strike - spot) / spot
            long_call_delta = max(0.1, 0.5 * np.exp(-long_moneyness * 5))
            
            legs.append({
                'type': 'BUY_CALL',
                'strike': long_call_strike,
                'premium': long_call_premium,
                'quantity': long_call_quantity,
                'delta': long_call_delta,
                'label': 'LONG_CALL_BACKSPREAD'
            })
            
            # Calculate net cost (debit if positive, credit if negative)
            net_cost = long_call_cost - short_call_credit
            
            # Check if within max debit constraint
            max_debit = spot * self.max_debit_pct
            if net_cost > max_debit:
                return None
            
            # Calculate net delta (should be positive for bullish)
            net_delta = (short_call_delta * self.lot_size) + (long_call_delta * long_call_quantity)
            
            return {
                'legs': legs,
                'net_cost': net_cost,
                'net_delta': net_delta,
                'short_call_strike': short_call_strike,
                'long_call_strike': long_call_strike,
                'spot': spot,
                'expiry_date': expiry_date
            }
            
        except Exception as e:
            return None
    
    def calculate_position_value(self, current_bar, historical_data):
        """Calculate current value of position"""
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            total_value = 0
            
            for leg in self.options_legs:
                strike = leg['strike']
                
                current_premium = self.get_premium_value(
                    strike, 'CE', current_date, 
                    self.option_expiry_date, spot, atr
                )
                
                # Long positions: positive value, Short positions: negative value
                if leg['type'] == 'BUY_CALL':
                    leg_value = current_premium * leg['quantity']
                else:  # SELL_CALL
                    leg_value = -current_premium * leg['quantity']
                
                total_value += leg_value
            
            return total_value
            
        except Exception as e:
            return None
    
    def on_data(self, data):
        """Main strategy logic"""
        if len(data) < 30:
            return None
        
        current_bar = data.iloc[-1]
        historical_data = data.iloc[:-1]
        
        # Entry logic
        if self.position is None:
            if self.should_enter(data):
                backspread_position = self.build_carry_backspread(current_bar, historical_data)
                
                if backspread_position is not None:
                    self.position = 'CARRY_BACKSPREAD'
                    self.entry_cost = backspread_position['net_cost']
                    self.entry_date = current_bar['date']
                    self.entry_spot = backspread_position['spot']
                    self.options_legs = backspread_position['legs']
                    self.short_call_strike = backspread_position['short_call_strike']
                    self.long_call_strike = backspread_position['long_call_strike']
                    self.net_delta = backspread_position['net_delta']
                    self.position_id += 1
                    
                    cost_type = "Debit" if self.entry_cost > 0 else "Credit"
                    
                    print(f"\n=== ENTERING BULLISH CARRY + CALL BACKSPREAD ===")
                    print(f"Date: {self.entry_date}")
                    print(f"Spot: {self.entry_spot:.2f}")
                    print(f"Net {cost_type}: ₹{abs(self.entry_cost):.2f}")
                    print(f"Net Delta: {self.net_delta:.3f}")
                    print(f"Short Call Strike: {self.short_call_strike}")
                    print(f"Long Call Strike: {self.long_call_strike}")
                    
                    for leg in self.options_legs:
                        print(f"  {leg['label']}: {leg['type']} {leg['quantity']} @ {leg['strike']} - Premium: ₹{leg['premium']:.2f}")
                    
                    self.trade_log.append({
                        'date': self.entry_date,
                        'action': 'ENTER_BACKSPREAD',
                        'spot': self.entry_spot,
                        'cost': self.entry_cost,
                        'debit': abs(self.entry_cost) if self.entry_cost > 0 else 0,
                        'credit': abs(self.entry_cost) if self.entry_cost < 0 else 0,
                        'net_delta': self.net_delta,
                        'short_strike': self.short_call_strike,
                        'long_strike': self.long_call_strike,
                        'position_id': self.position_id,
                        'legs': self.options_legs.copy()
                    })
                    
                    return None
        
        # Exit logic
        elif self.position == 'CARRY_BACKSPREAD':
            days_held = (current_bar['date'] - self.entry_date).days
            
            # Calculate current P&L
            position_value = self.calculate_position_value(current_bar, historical_data)
            
            if position_value is not None:
                # P&L = current value - initial cost
                pnl = position_value - self.entry_cost
                pnl_pct = pnl / abs(self.entry_cost) if abs(self.entry_cost) > 0 else pnl / self.entry_spot
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                # Time-based exit
                if days_held >= self.hold_days:
                    should_exit = True
                    exit_reason = "TIME"
                
                # Profit target
                elif abs(self.entry_cost) > 0 and pnl >= abs(self.entry_cost) * self.profit_target_pct:
                    should_exit = True
                    exit_reason = "PROFIT_TARGET"
                
                # Stop loss (especially important in danger zone between strikes)
                elif pnl <= -abs(max(self.entry_cost, self.entry_spot * 0.01)) * self.stop_loss_pct:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                
                # Check if price is in danger zone (between strikes) near expiry
                elif days_held >= self.hold_days - 2:
                    if self.short_call_strike <= current_bar['close'] <= self.long_call_strike:
                        should_exit = True
                        exit_reason = "DANGER_ZONE"
                
                if should_exit:
                    print(f"\n=== EXITING BULLISH CARRY + CALL BACKSPREAD ===")
                    print(f"Exit Date: {current_bar['date']}")
                    print(f"Exit Spot: {current_bar['close']:.2f}")
                    print(f"Days Held: {days_held}")
                    print(f"Exit Reason: {exit_reason}")
                    print(f"Entry Cost: ₹{self.entry_cost:.2f}")
                    print(f"Position Value: ₹{position_value:.2f}")
                    print(f"P&L: ₹{pnl:.2f} ({pnl_pct*100:.2f}%)")
                    
                    self.trade_log.append({
                        'date': current_bar['date'],
                        'action': 'EXIT_BACKSPREAD',
                        'spot': current_bar['close'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'days_held': days_held,
                        'exit_reason': exit_reason,
                        'position_id': self.position_id,
                        'legs': self.options_legs.copy()
                    })
                    
                    # Reset position
                    self.position = None
                    self.entry_cost = None
                    self.entry_date = None
                    self.entry_spot = None
                    self.options_legs = []
                    self.short_call_strike = None
                    self.long_call_strike = None
                    self.net_delta = 0
                    
                    return {
                        'type': 'EXIT',
                        'pnl': pnl,
                        'exit_reason': exit_reason
                    }
        
        return None
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal (required by backtest engine)"""
        result = self.on_data(pd.concat([historical_data, pd.DataFrame([current_bar])], ignore_index=True))
        
        if result is None:
            return 'HOLD'
        elif result.get('type') == 'EXIT':
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_trade_log(self):
        """Return trade log"""
        return self.trade_log
