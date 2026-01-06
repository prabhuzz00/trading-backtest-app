"""
Short Vol Inventory (Strike Grid) Options Strategy

This strategy implements a Short Volatility Inventory approach using a strike grid:
- SELLS multiple out-of-the-money (OTM) options across a grid of strikes
- Maintains a portfolio of short volatility positions
- Systematically sells options at various strike levels
- Collects premium from multiple positions

The strategy profits from theta decay across multiple strikes and benefits from
mean reversion and range-bound markets.

Strategy Characteristics:
- Maximum Profit: Total premium collected from all grid positions
- Maximum Loss: Unlimited (requires careful position sizing)
- Breakeven: Various levels depending on grid strikes
- Best Used: In stable, low volatility markets
- Benefits from: Time decay (theta), low realized volatility

Risk Management:
- Size positions appropriately across grid
- Use stop losses on individual legs
- Monitor aggregate delta exposure
- Consider rolling positions as they decay
- Exit before large volatility events

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 7)
    - num_strikes: Number of strikes in grid (default: 5)
    - strike_spacing_pct: % spacing between strikes (default: 0.02 = 2%)
    - sell_both_sides: Sell both calls and puts (default: True)
    - profit_target_pct: Exit profit % per position (default: 0.60 = 60%)
    - stop_loss_pct: Exit loss % per position (default: 2.0 = 200%)
    - delta_per_leg: Target delta per leg (default: 0.15)
    - max_aggregate_delta: Maximum net delta (default: 0.5)
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
    Short Vol Inventory - A multi-strike short volatility strategy
    
    Position Structure:
    1. SELL multiple OTM calls at different strikes
    2. SELL multiple OTM puts at different strikes
    3. Maintain a grid of short premium positions
    
    Collects premium across multiple strikes, profits from theta decay and
    range-bound markets.
    """
    
    def __init__(self, 
                 entry_day=None,
                 hold_days=7,
                 num_strikes=5,
                 strike_spacing_pct=0.02,  # 2% between strikes
                 sell_both_sides=True,
                 profit_target_pct=0.60,
                 stop_loss_pct=2.0,
                 delta_per_leg=0.15,
                 max_aggregate_delta=0.5,
                 strike_step=5000,  # 50 points in paise
                 lot_size=75,
                 min_days_to_expiry=7,
                 max_days_to_expiry=30,
                 iv_percentile_max=80):
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.num_strikes = num_strikes
        self.strike_spacing_pct = strike_spacing_pct
        self.sell_both_sides = sell_both_sides
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.delta_per_leg = delta_per_leg
        self.max_aggregate_delta = max_aggregate_delta
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.iv_percentile_max = iv_percentile_max
        
        # Position tracking
        self.position = None  # 'SHORT_GRID' when position is active
        self.entry_credit = None  # Total net credit received
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of all option legs in grid
        self.position_id = 0
        self.max_profit = 0  # Maximum profit (total credit)
        self.aggregate_delta = 0
        
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
        """Check if conditions are met to enter grid"""
        if self.position is not None:
            return False
        
        if len(data) < 30:
            return False
        
        return True
    
    def build_strike_grid(self, current_bar, historical_data):
        """Build strike grid with multiple short options"""
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
            
            # Build call side of grid
            for i in range(self.num_strikes):
                spacing_multiplier = (i + 1)
                call_strike = self.round_to_strike(spot * (1 + self.strike_spacing_pct * spacing_multiplier))
                
                call_premium = self.get_premium_value(call_strike, 'CE', current_date, expiry_date, spot, atr)
                
                if call_premium > 0:
                    # Estimate delta (simple approximation)
                    moneyness = (call_strike - spot) / spot
                    call_delta = -max(0.05, 0.5 * np.exp(-moneyness * 5))
                    
                    legs.append({
                        'type': 'SELL_CALL',
                        'strike': call_strike,
                        'premium': call_premium,
                        'quantity': self.lot_size,
                        'delta': call_delta
                    })
                    
                    total_credit += call_premium * self.lot_size
                    net_delta += call_delta * self.lot_size
            
            # Build put side of grid (if enabled)
            if self.sell_both_sides:
                for i in range(self.num_strikes):
                    spacing_multiplier = (i + 1)
                    put_strike = self.round_to_strike(spot * (1 - self.strike_spacing_pct * spacing_multiplier))
                    
                    put_premium = self.get_premium_value(put_strike, 'PE', current_date, expiry_date, spot, atr)
                    
                    if put_premium > 0:
                        # Estimate delta
                        moneyness = (spot - put_strike) / spot
                        put_delta = min(-0.05, -0.5 * np.exp(-moneyness * 5))
                        
                        legs.append({
                            'type': 'SELL_PUT',
                            'strike': put_strike,
                            'premium': put_premium,
                            'quantity': self.lot_size,
                            'delta': put_delta
                        })
                        
                        total_credit += put_premium * self.lot_size
                        net_delta += put_delta * self.lot_size
            
            if len(legs) == 0 or total_credit == 0:
                return None
            
            # Normalize delta per lot
            aggregate_delta = net_delta / self.lot_size
            
            # Check aggregate delta constraint
            if abs(aggregate_delta) > self.max_aggregate_delta:
                return None
            
            return {
                'legs': legs,
                'total_credit': total_credit,
                'aggregate_delta': aggregate_delta,
                'spot': spot,
                'expiry_date': expiry_date
            }
            
        except Exception as e:
            return None
    
    def calculate_position_value(self, current_bar, historical_data):
        """Calculate current value of all legs in grid"""
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            total_value = 0
            
            for leg in self.options_legs:
                strike = leg['strike']
                option_type = 'CE' if leg['type'] == 'SELL_CALL' else 'PE'
                
                current_premium = self.get_premium_value(
                    strike, option_type, current_date, 
                    self.option_expiry_date, spot, atr
                )
                
                # For short positions, value is negative of premium
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
                grid_position = self.build_strike_grid(current_bar, historical_data)
                
                if grid_position is not None:
                    self.position = 'SHORT_GRID'
                    self.entry_credit = grid_position['total_credit']
                    self.entry_date = current_bar['date']
                    self.entry_spot = grid_position['spot']
                    self.options_legs = grid_position['legs']
                    self.max_profit = self.entry_credit
                    self.aggregate_delta = grid_position['aggregate_delta']
                    self.position_id += 1
                    
                    print(f"\n=== ENTERING SHORT VOL GRID ===")
                    print(f"Date: {self.entry_date}")
                    print(f"Spot: {self.entry_spot:.2f}")
                    print(f"Total Credit: ₹{self.entry_credit:.2f}")
                    print(f"Aggregate Delta: {self.aggregate_delta:.3f}")
                    print(f"Number of Legs: {len(self.options_legs)}")
                    
                    for i, leg in enumerate(self.options_legs):
                        print(f"  Leg {i+1}: {leg['type']} @ {leg['strike']} - Premium: ₹{leg['premium']:.2f}")
                    
                    self.trade_log.append({
                        'date': self.entry_date,
                        'action': 'ENTER_GRID',
                        'spot': self.entry_spot,
                        'credit': self.entry_credit,
                        'num_legs': len(self.options_legs),
                        'aggregate_delta': self.aggregate_delta,
                        'position_id': self.position_id,
                        'legs': self.options_legs.copy()
                    })
                    
                    return None
        
        # Exit logic
        elif self.position == 'SHORT_GRID':
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
                    print(f"\n=== EXITING SHORT VOL GRID ===")
                    print(f"Exit Date: {current_bar['date']}")
                    print(f"Days Held: {days_held}")
                    print(f"Exit Reason: {exit_reason}")
                    print(f"Entry Credit: ₹{self.entry_credit:.2f}")
                    print(f"Exit Cost: ₹{-position_value:.2f}")
                    print(f"P&L: ₹{pnl:.2f} ({pnl_pct*100:.2f}%)")
                    
                    self.trade_log.append({
                        'date': current_bar['date'],
                        'action': 'EXIT_GRID',
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
                    self.aggregate_delta = 0
                    
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
