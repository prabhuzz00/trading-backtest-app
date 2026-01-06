"""
Tail Wing Hedge Options Strategy

This strategy implements a Tail Wing Hedge (also called Tail Risk Hedge):
- BUYS far out-of-the-money (OTM) put options for downside protection
- SELLS near-ATM options to finance the hedge (creates a "wing")
- Provides asymmetric protection against tail risk events
- Low cost or even credit-generating hedge

The strategy provides portfolio insurance against severe market declines while
minimizing the cost through premium collection from shorter-dated or near-ATM sales.

Strategy Characteristics:
- Maximum Profit: Significant if market crashes (long far OTM puts)
- Maximum Loss: Limited to net debit or small credit
- Breakeven: Depends on wing structure
- Best Used: For tail risk protection in bull markets
- Benefits from: Large market moves (especially downside)

Risk Management:
- Size tail hedge appropriately (typically 1-5% of portfolio)
- Roll wings as they decay
- Monitor overall delta exposure
- Consider calendar spreads for financing
- Exit or roll before major volatility events

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 14)
    - tail_strike_pct: % below spot for tail hedge (default: 0.10 = 10%)
    - wing_strike_pct: % below spot for wing (default: 0.03 = 3%)
    - wing_ratio: Ratio of wings to tail hedge (default: 2.0)
    - max_debit_pct: Maximum net debit as % of spot (default: 0.005 = 0.5%)
    - profit_target_multiple: Exit profit multiple (default: 3.0)
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
    Tail Wing Hedge - Asymmetric tail risk protection strategy
    
    Position Structure:
    1. BUY 1x far OTM Put (tail hedge) - 10% below spot
    2. SELL 2x near ATM Put (wing) - 3% below spot
    
    Provides downside protection with low cost by selling wings to finance tail hedge.
    """
    
    def __init__(self, 
                 entry_day=None,
                 hold_days=14,
                 tail_strike_pct=0.10,
                 wing_strike_pct=0.03,
                 wing_ratio=2.0,
                 max_debit_pct=0.005,
                 profit_target_multiple=3.0,
                 strike_step=5000,
                 lot_size=75,
                 min_days_to_expiry=14,
                 max_days_to_expiry=45,
                 iv_percentile_min=30):
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.tail_strike_pct = tail_strike_pct
        self.wing_strike_pct = wing_strike_pct
        self.wing_ratio = wing_ratio
        self.max_debit_pct = max_debit_pct
        self.profit_target_multiple = profit_target_multiple
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.iv_percentile_min = iv_percentile_min
        
        # Position tracking
        self.position = None  # 'TAIL_HEDGE' when position is active
        self.entry_cost = None  # Net debit/credit
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of all legs
        self.position_id = 0
        self.tail_strike = None
        self.wing_strike = None
        
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
        """Get next monthly expiry for tail hedge (longer dated)"""
        current_date_obj = pd.to_datetime(current_date)
        
        # Find next Thursday (weekly) but prefer monthly for tail hedge
        days_ahead = 3 - current_date_obj.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        next_expiry = current_date_obj + timedelta(days=days_ahead)
        
        # Add extra weeks to get to monthly-like expiry (3-4 weeks out)
        next_expiry += timedelta(days=14)
        
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
            if moneyness > 0:  # OTM
                intrinsic = 0
                # Far OTM puts have higher implied vol (volatility skew)
                skew_factor = 1.0 + abs(moneyness) * 0.5
                extrinsic = spot * iv_estimate * skew_factor * time_factor * np.exp(-moneyness * 2)
            else:  # ITM
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
        """Check if conditions are met to enter tail hedge"""
        if self.position is not None:
            return False
        
        if len(data) < 30:
            return False
        
        return True
    
    def build_tail_hedge(self, current_bar, historical_data):
        """Build tail wing hedge structure"""
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            expiry_date = self.get_next_expiry(current_date)
            self.option_expiry_date = expiry_date
            
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            legs = []
            
            # 1. BUY far OTM put (tail hedge)
            tail_strike = self.round_to_strike(spot * (1 - self.tail_strike_pct))
            tail_premium = self.get_premium_value(tail_strike, 'PE', current_date, expiry_date, spot, atr)
            
            if tail_premium <= 0:
                return None
            
            tail_cost = tail_premium * self.lot_size
            
            legs.append({
                'type': 'BUY_PUT',
                'strike': tail_strike,
                'premium': tail_premium,
                'quantity': self.lot_size,
                'label': 'TAIL_HEDGE'
            })
            
            # 2. SELL near ATM puts (wing to finance)
            wing_strike = self.round_to_strike(spot * (1 - self.wing_strike_pct))
            wing_premium = self.get_premium_value(wing_strike, 'PE', current_date, expiry_date, spot, atr)
            
            if wing_premium <= 0:
                return None
            
            wing_quantity = int(self.lot_size * self.wing_ratio)
            wing_credit = wing_premium * wing_quantity
            
            legs.append({
                'type': 'SELL_PUT',
                'strike': wing_strike,
                'premium': wing_premium,
                'quantity': wing_quantity,
                'label': 'WING'
            })
            
            # Calculate net cost (debit if positive, credit if negative)
            net_cost = tail_cost - wing_credit
            
            # Check if within max debit constraint
            max_debit = spot * self.max_debit_pct
            if net_cost > max_debit:
                # Try to adjust wing ratio to reduce cost
                return None
            
            return {
                'legs': legs,
                'net_cost': net_cost,
                'tail_strike': tail_strike,
                'wing_strike': wing_strike,
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
                    strike, 'PE', current_date, 
                    self.option_expiry_date, spot, atr
                )
                
                # Long positions: positive value, Short positions: negative value
                if leg['type'] == 'BUY_PUT':
                    leg_value = current_premium * leg['quantity']
                else:  # SELL_PUT
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
                hedge_position = self.build_tail_hedge(current_bar, historical_data)
                
                if hedge_position is not None:
                    self.position = 'TAIL_HEDGE'
                    self.entry_cost = hedge_position['net_cost']
                    self.entry_date = current_bar['date']
                    self.entry_spot = hedge_position['spot']
                    self.options_legs = hedge_position['legs']
                    self.tail_strike = hedge_position['tail_strike']
                    self.wing_strike = hedge_position['wing_strike']
                    self.position_id += 1
                    
                    print(f"\n=== ENTERING TAIL WING HEDGE ===")
                    print(f"Date: {self.entry_date}")
                    print(f"Spot: {self.entry_spot:.2f}")
                    print(f"Net Cost: ₹{self.entry_cost:.2f}")
                    print(f"Tail Strike: {self.tail_strike}")
                    print(f"Wing Strike: {self.wing_strike}")
                    
                    for leg in self.options_legs:
                        print(f"  {leg['label']}: {leg['type']} {leg['quantity']} @ {leg['strike']} - Premium: ₹{leg['premium']:.2f}")
                    
                    self.trade_log.append({
                        'date': self.entry_date,
                        'action': 'ENTER_HEDGE',
                        'spot': self.entry_spot,
                        'cost': self.entry_cost,
                        'debit': abs(self.entry_cost) if self.entry_cost > 0 else 0,
                        'credit': abs(self.entry_cost) if self.entry_cost < 0 else 0,
                        'tail_strike': self.tail_strike,
                        'wing_strike': self.wing_strike,
                        'position_id': self.position_id,
                        'legs': self.options_legs.copy()
                    })
                    
                    return None
        
        # Exit logic
        elif self.position == 'TAIL_HEDGE':
            days_held = (current_bar['date'] - self.entry_date).days
            
            # Calculate current P&L
            position_value = self.calculate_position_value(current_bar, historical_data)
            
            if position_value is not None:
                # P&L = current value - initial cost
                pnl = position_value - self.entry_cost
                pnl_multiple = pnl / abs(self.entry_cost) if self.entry_cost != 0 else 0
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                # Time-based exit
                if days_held >= self.hold_days:
                    should_exit = True
                    exit_reason = "TIME"
                
                # Profit target (tail hedge paid off significantly)
                elif pnl > abs(self.entry_cost) * self.profit_target_multiple:
                    should_exit = True
                    exit_reason = "PROFIT_TARGET"
                
                # Check if tail is deep ITM (market crashed)
                elif current_bar['close'] < self.tail_strike:
                    should_exit = True
                    exit_reason = "TAIL_ITM"
                
                if should_exit:
                    print(f"\n=== EXITING TAIL WING HEDGE ===")
                    print(f"Exit Date: {current_bar['date']}")
                    print(f"Days Held: {days_held}")
                    print(f"Exit Reason: {exit_reason}")
                    print(f"Entry Cost: ₹{self.entry_cost:.2f}")
                    print(f"Position Value: ₹{position_value:.2f}")
                    print(f"P&L: ₹{pnl:.2f} ({pnl_multiple:.2f}x)")
                    
                    self.trade_log.append({
                        'date': current_bar['date'],
                        'action': 'EXIT_HEDGE',
                        'spot': current_bar['close'],
                        'pnl': pnl,
                        'pnl_pct': pnl_multiple,
                        'pnl_multiple': pnl_multiple,
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
                    self.tail_strike = None
                    self.wing_strike = None
                    
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
