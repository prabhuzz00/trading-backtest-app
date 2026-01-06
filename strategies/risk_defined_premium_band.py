"""
Risk-Defined Short Premium Band Options Strategy

This strategy implements a Risk-Defined Short Premium Band (Iron Condor variant):
- SELLS an OTM call vertical spread (define upside risk)
- SELLS an OTM put vertical spread (define downside risk)
- Creates a "band" or range where maximum profit occurs
- All risk is defined by the width of the spreads

The strategy profits from theta decay when the underlying stays within the band,
with clearly defined maximum loss on both sides.

Strategy Characteristics:
- Maximum Profit: Net premium collected
- Maximum Loss: Width of spread minus net premium
- Breakeven: Strike adjustments based on premium
- Best Used: In range-bound, low volatility markets
- Benefits from: Time decay (theta), stable price action

Risk Management:
- Risk is predefined by spread width
- Use appropriate position sizing
- Consider adjusting when tested
- Monitor volatility changes
- Exit at profit targets or manage tested sides

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 7)
    - band_width_pct: % width of profitable band (default: 0.10 = 10%)
    - spread_width_pct: Width of each spread (default: 0.02 = 2%)
    - profit_target_pct: Exit profit % (default: 0.50 = 50%)
    - stop_loss_pct: Exit loss % (default: 2.0 = 200% of credit)
    - target_delta: Target delta for short strikes (default: 0.20)
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
    Risk-Defined Short Premium Band - Iron Condor-like structure
    
    Position Structure:
    1. SELL OTM Call + BUY further OTM Call (call spread)
    2. SELL OTM Put + BUY further OTM Put (put spread)
    
    Creates a band where profit is maximized, with defined risk on both sides.
    """
    
    def __init__(self, 
                 entry_day=None,
                 hold_days=7,
                 band_width_pct=0.10,
                 spread_width_pct=0.02,
                 profit_target_pct=0.50,
                 stop_loss_pct=2.0,
                 target_delta=0.20,
                 strike_step=5000,
                 lot_size=75,
                 min_days_to_expiry=7,
                 max_days_to_expiry=30,
                 iv_percentile_max=80):
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.band_width_pct = band_width_pct
        self.spread_width_pct = spread_width_pct
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.target_delta = target_delta
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.iv_percentile_max = iv_percentile_max
        
        # Position tracking
        self.position = None  # 'PREMIUM_BAND' when position is active
        self.entry_credit = None  # Net credit received
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of all legs
        self.position_id = 0
        self.max_profit = 0
        self.max_loss = 0
        
        # Strike tracking
        self.call_short_strike = None
        self.call_long_strike = None
        self.put_short_strike = None
        self.put_long_strike = None
        
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
        """Get option premium - first try real data from engine, then theoretical"""
        # Try to fetch real premium from engine if available
        if hasattr(self, '_engine_fetch_option_premium'):
            premium = self._engine_fetch_option_premium(strike, option_type, current_date, expiry_date)
            if premium is not None and premium > 0:
                return premium
        
        # Fallback to database query
        premium = self.fetch_option_premium(strike, option_type, current_date, expiry_date)
        if premium is not None and premium > 0:
            return premium
        
        # Last resort: theoretical estimation
        days_to_expiry = (pd.to_datetime(expiry_date) - pd.to_datetime(current_date)).days
        return self.estimate_premium_theoretical(spot, strike, atr, option_type, days_to_expiry)
    
    def should_enter(self, data):
        """Check if conditions are met to enter band"""
        if self.position is not None:
            return False
        
        if len(data) < 30:
            return False
        
        return True
    
    def build_premium_band(self, current_bar, historical_data):
        """Build risk-defined premium band (iron condor) using real strikes"""
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            # Get closest expiry from engine if available
            if hasattr(self, '_engine_get_closest_expiry'):
                expiry_date = self._engine_get_closest_expiry(current_date, min_days=7)
                if expiry_date is None:
                    # Fallback to calculated expiry
                    expiry_date = self.get_next_expiry(current_date)
            else:
                expiry_date = self.get_next_expiry(current_date)
            
            self.option_expiry_date = expiry_date
            
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            legs = []
            
            # Get available strikes from engine if available
            if hasattr(self, '_engine_get_available_strikes'):
                ce_strikes = self._engine_get_available_strikes(expiry_date, 'CE')
                pe_strikes = self._engine_get_available_strikes(expiry_date, 'PE')
                
                if not ce_strikes or not pe_strikes:
                    print(f"  Warning: No strikes available for {expiry_date}")
                    return None
                
                # Find ATM strike
                atm_strike = self._engine_find_atm_strike(spot, ce_strikes)
                
                # Call spread: OTM calls
                # Short call at band width from spot
                call_short_strike = self._engine_find_otm_call_strike(spot, ce_strikes, otm_pct=self.band_width_pct/2)
                # Long call at spread width above short
                call_long_target = call_short_strike * (1 + self.spread_width_pct)
                call_long_strike = min([s for s in ce_strikes if s >= call_long_target], default=call_short_strike)
                
                # Put spread: OTM puts
                # Short put at band width from spot
                put_short_strike = self._engine_find_otm_put_strike(spot, pe_strikes, otm_pct=self.band_width_pct/2)
                # Long put at spread width below short
                put_long_target = put_short_strike * (1 - self.spread_width_pct)
                put_long_strike = max([s for s in pe_strikes if s <= put_long_target], default=put_short_strike)
            else:
                # Fallback to calculated strikes
                half_band = self.band_width_pct / 2
                call_short_strike = self.round_to_strike(spot * (1 + half_band))
                call_long_strike = self.round_to_strike(spot * (1 + half_band + self.spread_width_pct))
                put_short_strike = self.round_to_strike(spot * (1 - half_band))
                put_long_strike = self.round_to_strike(spot * (1 - half_band - self.spread_width_pct))
            
            # Get premiums for call spread
            call_short_premium = self.get_premium_value(call_short_strike, 'CE', current_date, expiry_date, spot, atr)
            call_long_premium = self.get_premium_value(call_long_strike, 'CE', current_date, expiry_date, spot, atr)
            
            if call_short_premium <= 0 or call_long_premium <= 0:
                return None
            
            call_spread_credit = (call_short_premium - call_long_premium) * self.lot_size
            
            legs.append({
                'type': 'SELL_CALL',
                'strike': call_short_strike,
                'premium': call_short_premium,
                'quantity': self.lot_size,
                'label': 'CALL_SHORT'
            })
            
            legs.append({
                'type': 'BUY_CALL',
                'strike': call_long_strike,
                'premium': call_long_premium,
                'quantity': self.lot_size,
                'label': 'CALL_LONG'
            })
            
            # Get premiums for put spread
            put_short_premium = self.get_premium_value(put_short_strike, 'PE', current_date, expiry_date, spot, atr)
            put_long_premium = self.get_premium_value(put_long_strike, 'PE', current_date, expiry_date, spot, atr)
            
            if put_short_premium <= 0 or put_long_premium <= 0:
                return None
            
            put_spread_credit = (put_short_premium - put_long_premium) * self.lot_size
            
            legs.append({
                'type': 'SELL_PUT',
                'strike': put_short_strike,
                'premium': put_short_premium,
                'quantity': self.lot_size,
                'label': 'PUT_SHORT'
            })
            
            legs.append({
                'type': 'BUY_PUT',
                'strike': put_long_strike,
                'premium': put_long_premium,
                'quantity': self.lot_size,
                'label': 'PUT_LONG'
            })
            
            # Calculate net credit and max loss
            net_credit = call_spread_credit + put_spread_credit
            
            if net_credit <= 0:
                return None
            
            # Max loss is width of spread minus credit
            call_spread_width = call_long_strike - call_short_strike
            put_spread_width = put_short_strike - put_long_strike
            max_loss_call = (call_spread_width * self.lot_size) - call_spread_credit
            max_loss_put = (put_spread_width * self.lot_size) - put_spread_credit
            max_loss = max(max_loss_call, max_loss_put)
            
            return {
                'legs': legs,
                'net_credit': net_credit,
                'max_loss': max_loss,
                'call_short_strike': call_short_strike,
                'call_long_strike': call_long_strike,
                'put_short_strike': put_short_strike,
                'put_long_strike': put_long_strike,
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
                band_position = self.build_premium_band(current_bar, historical_data)
                
                if band_position is not None:
                    self.position = 'PREMIUM_BAND'
                    self.entry_credit = band_position['net_credit']
                    self.entry_date = current_bar['date']
                    self.entry_spot = band_position['spot']
                    self.options_legs = band_position['legs']
                    self.max_profit = self.entry_credit
                    self.max_loss = band_position['max_loss']
                    self.call_short_strike = band_position['call_short_strike']
                    self.call_long_strike = band_position['call_long_strike']
                    self.put_short_strike = band_position['put_short_strike']
                    self.put_long_strike = band_position['put_long_strike']
                    self.position_id += 1
                    
                    print(f"\n=== ENTERING PREMIUM BAND ===")
                    print(f"Date: {self.entry_date}")
                    print(f"Spot: {self.entry_spot:.2f}")
                    print(f"Net Credit: ₹{self.entry_credit:.2f}")
                    print(f"Max Profit: ₹{self.max_profit:.2f}")
                    print(f"Max Loss: ₹{self.max_loss:.2f}")
                    print(f"Call Spread: {self.call_short_strike}/{self.call_long_strike}")
                    print(f"Put Spread: {self.put_short_strike}/{self.put_long_strike}")
                    
                    self.trade_log.append({
                        'date': self.entry_date,
                        'action': 'ENTER_BAND',
                        'spot': self.entry_spot,
                        'credit': self.entry_credit,
                        'max_loss': self.max_loss,
                        'position_id': self.position_id,
                        'legs': self.options_legs.copy()
                    })
                    
                    return None
        
        # Exit logic
        elif self.position == 'PREMIUM_BAND':
            days_held = (current_bar['date'] - self.entry_date).days
            
            # Calculate current P&L
            position_value = self.calculate_position_value(current_bar, historical_data)
            
            if position_value is not None:
                # For credit spread, P&L = credit received + position value (negative)
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
                
                # Check if price breaches band significantly
                elif current_bar['close'] >= self.call_long_strike or current_bar['close'] <= self.put_long_strike:
                    should_exit = True
                    exit_reason = "BAND_BREACH"
                
                if should_exit:
                    print(f"\n=== EXITING PREMIUM BAND ===")
                    print(f"Exit Date: {current_bar['date']}")
                    print(f"Exit Spot: {current_bar['close']:.2f}")
                    print(f"Days Held: {days_held}")
                    print(f"Exit Reason: {exit_reason}")
                    print(f"Entry Credit: ₹{self.entry_credit:.2f}")
                    print(f"Exit Cost: ₹{-position_value:.2f}")
                    print(f"P&L: ₹{pnl:.2f} ({pnl_pct*100:.2f}%)")
                    
                    self.trade_log.append({
                        'date': current_bar['date'],
                        'action': 'EXIT_BAND',
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
                    self.max_profit = 0
                    self.max_loss = 0
                    
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
