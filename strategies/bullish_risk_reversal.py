"""
Bullish Risk Reversal Options Strategy

This strategy implements a Bullish Risk Reversal (also called Collar for bullish bias):
- BUYS an out-of-the-money (OTM) call option (upside participation)
- SELLS an out-of-the-money (OTM) put option (finances the call)
- Synthetic long position with defined downside risk
- Low cost or zero cost structure

The strategy provides bullish exposure with limited downside while maintaining
upside potential, often used for directional trades or as a hedge.

Strategy Characteristics:
- Maximum Profit: Unlimited (above call strike)
- Maximum Loss: Limited to put strike (minus net credit/plus net debit)
- Breakeven: Call strike + net debit (or - net credit)
- Best Used: In bullish markets with moderate volatility
- Benefits from: Upward price movement, long delta exposure

Risk Management:
- Monitor downside risk at put strike
- Size position appropriately
- Consider rolling positions
- Use stop losses if put is tested
- Exit before adverse moves

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 10)
    - call_otm_pct: % above spot for call strike (default: 0.05 = 5%)
    - put_otm_pct: % below spot for put strike (default: 0.05 = 5%)
    - max_debit_pct: Maximum net debit as % of spot (default: 0.01 = 1%)
    - profit_target_pct: Exit profit % (default: 1.0 = 100%)
    - stop_loss_pct: Exit loss % (default: 0.50 = 50%)
    - call_delta_target: Target delta for call (default: 0.40)
    - put_delta_target: Target delta for put (default: -0.40)
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
    Bullish Risk Reversal - Synthetic long with defined risk
    
    Position Structure:
    1. BUY 1 OTM Call (upside participation)
    2. SELL 1 OTM Put (finances call, creates downside risk)
    
    Provides bullish exposure with limited cost, ideal for directional trades.
    """
    
    def __init__(self, 
                 entry_day=None,
                 hold_days=10,
                 call_otm_pct=0.05,
                 put_otm_pct=0.05,
                 max_debit_pct=0.01,
                 profit_target_pct=1.0,
                 stop_loss_pct=0.50,
                 call_delta_target=0.40,
                 put_delta_target=-0.40,
                 strike_step=5000,
                 lot_size=75,
                 min_days_to_expiry=7,
                 max_days_to_expiry=30,
                 momentum_lookback=10):
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.call_otm_pct = call_otm_pct
        self.put_otm_pct = put_otm_pct
        self.max_debit_pct = max_debit_pct
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.call_delta_target = call_delta_target
        self.put_delta_target = put_delta_target
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.momentum_lookback = momentum_lookback
        
        # Position tracking
        self.position = None  # 'RISK_REVERSAL' when position is active
        self.entry_cost = None  # Net debit/credit
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of all legs
        self.position_id = 0
        self.call_strike = None
        self.put_strike = None
        self.net_delta = 0
        
        # Trade log for detailed reporting
        self.trade_log = []
        
        # Underlying symbol tracking
        self.underlying_symbol = None
        self.option_expiry_date = None
        
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
        """Check if conditions are met to enter risk reversal"""
        if self.position is not None:
            return False
        
        if len(data) < max(self.momentum_lookback + 1, 30):
            return False
        
        # Check for bullish momentum
        historical_data = data.iloc[:-1]
        momentum = self.calculate_momentum(historical_data)
        
        # Require positive momentum for bullish setup
        if momentum <= 0:
            return False
        
        return True
    
    def build_risk_reversal(self, current_bar, historical_data):
        """Build bullish risk reversal position"""
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            expiry_date = self.get_next_expiry(current_date)
            self.option_expiry_date = expiry_date
            
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            legs = []
            
            # 1. BUY OTM Call
            call_strike = self.round_to_strike(spot * (1 + self.call_otm_pct))
            call_premium = self.get_premium_value(call_strike, 'CE', current_date, expiry_date, spot, atr)
            
            if call_premium <= 0:
                return None
            
            call_cost = call_premium * self.lot_size
            
            # Estimate call delta
            call_moneyness = (call_strike - spot) / spot
            call_delta = max(0.1, 0.5 * np.exp(-call_moneyness * 5))
            
            legs.append({
                'type': 'BUY_CALL',
                'strike': call_strike,
                'premium': call_premium,
                'quantity': self.lot_size,
                'delta': call_delta,
                'label': 'LONG_CALL'
            })
            
            # 2. SELL OTM Put (to finance)
            put_strike = self.round_to_strike(spot * (1 - self.put_otm_pct))
            put_premium = self.get_premium_value(put_strike, 'PE', current_date, expiry_date, spot, atr)
            
            if put_premium <= 0:
                return None
            
            put_credit = put_premium * self.lot_size
            
            # Estimate put delta
            put_moneyness = (spot - put_strike) / spot
            put_delta = min(-0.1, -0.5 * np.exp(-put_moneyness * 5))
            
            legs.append({
                'type': 'SELL_PUT',
                'strike': put_strike,
                'premium': put_premium,
                'quantity': self.lot_size,
                'delta': put_delta,
                'label': 'SHORT_PUT'
            })
            
            # Calculate net cost (debit if positive, credit if negative)
            net_cost = call_cost - put_credit
            
            # Check if within max debit constraint
            max_debit = spot * self.max_debit_pct
            if net_cost > max_debit:
                return None
            
            # Calculate net delta (should be positive for bullish)
            net_delta = (call_delta * self.lot_size) + (put_delta * self.lot_size)
            
            return {
                'legs': legs,
                'net_cost': net_cost,
                'net_delta': net_delta,
                'call_strike': call_strike,
                'put_strike': put_strike,
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
                option_type = 'CE' if 'CALL' in leg['type'] else 'PE'
                
                current_premium = self.get_premium_value(
                    strike, option_type, current_date, 
                    self.option_expiry_date, spot, atr
                )
                
                # Long positions: positive value, Short positions: negative value
                if 'BUY' in leg['type']:
                    leg_value = current_premium * leg['quantity']
                else:  # SELL
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
                reversal_position = self.build_risk_reversal(current_bar, historical_data)
                
                if reversal_position is not None:
                    self.position = 'RISK_REVERSAL'
                    self.entry_cost = reversal_position['net_cost']
                    self.entry_date = current_bar['date']
                    self.entry_spot = reversal_position['spot']
                    self.options_legs = reversal_position['legs']
                    self.call_strike = reversal_position['call_strike']
                    self.put_strike = reversal_position['put_strike']
                    self.net_delta = reversal_position['net_delta']
                    self.position_id += 1
                    
                    cost_type = "Debit" if self.entry_cost > 0 else "Credit"
                    
                    print(f"\n=== ENTERING BULLISH RISK REVERSAL ===")
                    print(f"Date: {self.entry_date}")
                    print(f"Spot: {self.entry_spot:.2f}")
                    print(f"Net {cost_type}: ₹{abs(self.entry_cost):.2f}")
                    print(f"Net Delta: {self.net_delta:.3f}")
                    print(f"Call Strike: {self.call_strike}")
                    print(f"Put Strike: {self.put_strike}")
                    
                    for leg in self.options_legs:
                        print(f"  {leg['label']}: {leg['type']} @ {leg['strike']} - Premium: ₹{leg['premium']:.2f}")
                    
                    self.trade_log.append({
                        'date': self.entry_date,
                        'action': 'ENTER_REVERSAL',
                        'spot': self.entry_spot,
                        'cost': self.entry_cost,
                        'debit': abs(self.entry_cost) if self.entry_cost > 0 else 0,
                        'credit': abs(self.entry_cost) if self.entry_cost < 0 else 0,
                        'net_delta': self.net_delta,
                        'call_strike': self.call_strike,
                        'put_strike': self.put_strike,
                        'position_id': self.position_id,
                        'legs': self.options_legs.copy()
                    })
                    
                    return None
        
        # Exit logic
        elif self.position == 'RISK_REVERSAL':
            days_held = (current_bar['date'] - self.entry_date).days
            
            # Calculate current P&L
            position_value = self.calculate_position_value(current_bar, historical_data)
            
            if position_value is not None:
                # P&L = current value - initial cost
                pnl = position_value - self.entry_cost
                pnl_pct = pnl / abs(self.entry_cost) if self.entry_cost != 0 else pnl / self.entry_spot
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                # Time-based exit
                if days_held >= self.hold_days:
                    should_exit = True
                    exit_reason = "TIME"
                
                # Profit target
                elif self.entry_cost > 0 and pnl >= self.entry_cost * self.profit_target_pct:
                    should_exit = True
                    exit_reason = "PROFIT_TARGET"
                
                # Stop loss
                elif pnl <= -abs(self.entry_cost) * self.stop_loss_pct:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                
                # Check if put is tested (price fell below put strike)
                elif current_bar['close'] < self.put_strike:
                    should_exit = True
                    exit_reason = "PUT_TESTED"
                
                if should_exit:
                    print(f"\n=== EXITING BULLISH RISK REVERSAL ===")
                    print(f"Exit Date: {current_bar['date']}")
                    print(f"Exit Spot: {current_bar['close']:.2f}")
                    print(f"Days Held: {days_held}")
                    print(f"Exit Reason: {exit_reason}")
                    print(f"Entry Cost: ₹{self.entry_cost:.2f}")
                    print(f"Position Value: ₹{position_value:.2f}")
                    print(f"P&L: ₹{pnl:.2f} ({pnl_pct*100:.2f}%)")
                    
                    self.trade_log.append({
                        'date': current_bar['date'],
                        'action': 'EXIT_REVERSAL',
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
                    self.call_strike = None
                    self.put_strike = None
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
