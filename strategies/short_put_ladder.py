"""
Short Put Ladder/Strip Options Strategy

This strategy implements a Short Put Ladder (also called Put Strip):
- SELLS multiple put options at different strikes
- More contracts at lower strikes (ratio structure)
- Collects premium from multiple put sales
- Bearish to neutral bias with defined risk at each strike

The strategy profits from theta decay and benefits when the market stays above
the strikes. The "ladder" or "strip" structure means more contracts at lower strikes.

Strategy Characteristics:
- Maximum Profit: Total premium collected
- Maximum Loss: Strike prices minus premium (at each level)
- Breakeven: Various levels at each strike minus premium
- Best Used: In neutral to slightly bearish markets
- Benefits from: Time decay (theta), stable markets

Risk Management:
- Carefully size positions (more at lower strikes)
- Use stop losses on individual legs
- Monitor overall put exposure
- Consider delta-neutral hedging
- Exit before significant downward movement

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 7)
    - num_strikes: Number of put strikes (default: 3)
    - strike_spacing_pct: % spacing between strikes (default: 0.03 = 3%)
    - ratio_multiplier: Contract multiplier per level (default: 1.5)
    - profit_target_pct: Exit profit % (default: 0.60 = 60%)
    - stop_loss_pct: Exit loss % per position (default: 2.0 = 200%)
    - base_delta: Target delta for highest strike (default: 0.30)
    - strike_step: Strike price rounding step (default: 50)
    - lot_size: Base contract lot size (default: 75)
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
    Short Put Ladder - A ratio-based short put strategy
    
    Position Structure:
    1. SELL 1x Put at highest strike (near ATM)
    2. SELL 1.5x Put at middle strike (OTM)
    3. SELL 2x Put at lowest strike (further OTM)
    
    Collects premium from multiple put sales with increasing size at lower strikes.
    """
    
    def __init__(self, 
                 entry_day=None,
                 hold_days=7,
                 num_strikes=3,
                 strike_spacing_pct=0.03,
                 ratio_multiplier=1.5,
                 profit_target_pct=0.60,
                 stop_loss_pct=2.0,
                 base_delta=0.30,
                 strike_step=5000,
                 lot_size=75,
                 min_days_to_expiry=7,
                 max_days_to_expiry=30,
                 iv_percentile_max=80):
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.num_strikes = num_strikes
        self.strike_spacing_pct = strike_spacing_pct
        self.ratio_multiplier = ratio_multiplier
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.base_delta = base_delta
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.iv_percentile_max = iv_percentile_max
        
        # Position tracking
        self.position = None  # 'SHORT_PUT_LADDER' when position is active
        self.entry_credit = None  # Total net credit received
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of all put legs
        self.position_id = 0
        self.max_profit = 0  # Maximum profit (total credit)
        self.total_delta = 0
        
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
        
        if option_type == 'PE':
            moneyness = (spot - strike) / spot
            if moneyness > 0:
                intrinsic = 0
                extrinsic = spot * iv_estimate * time_factor * np.exp(-moneyness * 2)
            else:
                intrinsic = strike - spot
                extrinsic = spot * iv_estimate * time_factor * 0.5
        else:
            moneyness = (strike - spot) / spot
            if moneyness > 0:
                intrinsic = 0
                extrinsic = spot * iv_estimate * time_factor * np.exp(-moneyness * 2)
            else:
                intrinsic = spot - strike
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
        """Check if conditions are met to enter ladder"""
        if self.position is not None:
            return False
        
        if len(data) < 30:
            return False
        
        return True
    
    def build_put_ladder(self, current_bar, historical_data):
        """Build put ladder with ratio structure"""
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            expiry_date = self.get_next_expiry(current_date)
            self.option_expiry_date = expiry_date
            
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            legs = []
            total_credit = 0
            net_delta = 0
            
            # Build put ladder (more contracts at lower strikes)
            for i in range(self.num_strikes):
                # Calculate strike (going down from spot)
                spacing_multiplier = i
                put_strike = self.round_to_strike(spot * (1 - self.strike_spacing_pct * spacing_multiplier))
                
                # Calculate quantity (increasing ratio at lower strikes)
                quantity = int(self.lot_size * (self.ratio_multiplier ** i))
                
                put_premium = self.get_premium_value(put_strike, 'PE', current_date, expiry_date, spot, atr)
                
                if put_premium > 0:
                    # Estimate delta (simple approximation for puts)
                    moneyness = (spot - put_strike) / spot
                    if moneyness > 0:  # OTM
                        put_delta = min(-0.05, -0.5 * np.exp(-moneyness * 5))
                    else:  # ITM
                        put_delta = max(-0.95, -0.5 - 0.45 * (1 - np.exp(moneyness * 5)))
                    
                    legs.append({
                        'type': 'SELL_PUT',
                        'strike': put_strike,
                        'premium': put_premium,
                        'quantity': quantity,
                        'delta': put_delta,
                        'level': i + 1
                    })
                    
                    total_credit += put_premium * quantity
                    net_delta += put_delta * quantity
            
            if len(legs) == 0 or total_credit == 0:
                return None
            
            return {
                'legs': legs,
                'total_credit': total_credit,
                'total_delta': net_delta,
                'spot': spot,
                'expiry_date': expiry_date
            }
            
        except Exception as e:
            return None
    
    def calculate_position_value(self, current_bar, historical_data):
        """Calculate current value of all legs"""
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
                    strike, 'PE', current_date, 
                    self.option_expiry_date, spot, atr
                )
                
                # For short puts, value is negative of premium
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
                ladder_position = self.build_put_ladder(current_bar, historical_data)
                
                if ladder_position is not None:
                    self.position = 'SHORT_PUT_LADDER'
                    self.entry_credit = ladder_position['total_credit']
                    self.entry_date = current_bar['date']
                    self.entry_spot = ladder_position['spot']
                    self.options_legs = ladder_position['legs']
                    self.max_profit = self.entry_credit
                    self.total_delta = ladder_position['total_delta']
                    self.position_id += 1
                    
                    print(f"\n=== ENTERING SHORT PUT LADDER ===")
                    print(f"Date: {self.entry_date}")
                    print(f"Spot: {self.entry_spot:.2f}")
                    print(f"Total Credit: ₹{self.entry_credit:.2f}")
                    print(f"Total Delta: {self.total_delta:.3f}")
                    print(f"Number of Levels: {len(self.options_legs)}")
                    
                    for leg in self.options_legs:
                        print(f"  Level {leg['level']}: SELL {leg['quantity']} Puts @ {leg['strike']} - Premium: ₹{leg['premium']:.2f}")
                    
                    self.trade_log.append({
                        'date': self.entry_date,
                        'action': 'ENTER_LADDER',
                        'spot': self.entry_spot,
                        'credit': self.entry_credit,
                        'num_legs': len(self.options_legs),
                        'total_delta': self.total_delta,
                        'position_id': self.position_id,
                        'legs': self.options_legs.copy()
                    })
                    
                    return None
        
        # Exit logic
        elif self.position == 'SHORT_PUT_LADDER':
            days_held = (current_bar['date'] - self.entry_date).days
            
            # Calculate current P&L
            position_value = self.calculate_position_value(current_bar, historical_data)
            
            if position_value is not None:
                # For short positions, P&L = credit received + position value (negative)
                pnl = self.entry_credit + position_value
                pnl_pct = pnl / abs(self.entry_credit) if self.entry_credit != 0 else 0
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                # Time-based exit
                if days_held >= self.hold_days:
                    should_exit = True
                    exit_reason = "TIME"
                
                # Profit target
                elif pnl >= self.entry_credit * self.profit_target_pct:
                    should_exit = True
                    exit_reason = "PROFIT_TARGET"
                
                # Stop loss
                elif pnl <= -self.entry_credit * self.stop_loss_pct:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                
                if should_exit:
                    print(f"\n=== EXITING SHORT PUT LADDER ===")
                    print(f"Exit Date: {current_bar['date']}")
                    print(f"Days Held: {days_held}")
                    print(f"Exit Reason: {exit_reason}")
                    print(f"Entry Credit: ₹{self.entry_credit:.2f}")
                    print(f"Exit Cost: ₹{-position_value:.2f}")
                    print(f"P&L: ₹{pnl:.2f} ({pnl_pct*100:.2f}%)")
                    
                    self.trade_log.append({
                        'date': current_bar['date'],
                        'action': 'EXIT_LADDER',
                        'spot': current_bar['close'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'days_held': days_held,
                        'exit_reason': exit_reason,
                        'position_id': self.position_id,
                        'closing_cost': abs(position_value),
                        'legs': self.options_legs.copy()
                    })
                    
                    # Reset position
                    self.position = None
                    self.entry_credit = None
                    self.entry_date = None
                    self.entry_spot = None
                    self.options_legs = []
                    self.total_delta = 0
                    
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
