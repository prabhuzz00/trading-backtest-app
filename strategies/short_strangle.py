"""
Short Strangle Options Strategy

This strategy implements a Short Strangle, which is a neutral options strategy that:
- SELLS an out-of-the-money (OTM) call option
- SELLS an out-of-the-money (OTM) put option
- Both options have the same expiration date

The strategy benefits from THETA DECAY (time decay) and is profitable when the 
underlying stays within a range. Maximum profit is achieved when both options 
expire worthless.

Strategy Characteristics:
- Maximum Profit: Total premium received (credit)
- Maximum Loss: Unlimited (on both sides)
- Breakeven Points: Call strike + premium received, Put strike - premium received
- Best Used: In low volatility, range-bound markets
- Benefits from: Time decay (theta), decreasing volatility

Risk Management:
- Use stop losses to limit downside
- Consider closing at 50-75% of max profit
- Monitor volatility - avoid before major events
- Best in sideways markets with low IV

Parameters:
    - entry_day: Day of week to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold position (default: 7)
    - delta_target: Target delta for strike selection (default: 0.3)
    - call_delta: Call option delta target (default: -0.3)
    - put_delta: Put option delta target (default: 0.3)
    - strike_width_pct: % away from spot for strikes (default: 0.05 = 5%)
    - profit_target_pct: Exit profit % (default: 0.50 = 50% of max profit)
    - stop_loss_pct: Exit loss % (default: 2.0 = 200% of premium received)
    - iv_threshold: Maximum IV percentile to enter (default: 50)
    - strike_step: Strike price rounding step (default: 50)
    - lot_size: Contract lot size (default: 50)
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
    Short Strangle - A high-theta, neutral options strategy
    
    Position Structure:
    1. SELL 1 OTM Call (above current price)
    2. SELL 1 OTM Put (below current price)
    
    Collects premium from both options. Profits from time decay when price stays
    within the strikes.
    """
    
    def __init__(self, 
                 entry_day=None,  # None=any day (test mode), 0=Mon, 1=Tue, avoid 3=Thu (expiry)
                 hold_days=7,
                 strike_width_pct=0.05,  # 5% away from spot
                 profit_target_pct=0.50,  # Close at 50% of max profit
                 stop_loss_pct=2.0,  # Stop if loss exceeds 200% of credit
                 strike_step=5000,  # 50 points in paise (50 * 100)
                 lot_size=75,
                 iv_percentile_max=90,  # Very relaxed for testing: enter when IV < 90th percentile
                 atr_period=14,
                 min_days_to_expiry=7,  # Minimum DTE to enter
                 max_days_to_expiry=30):  # Maximum DTE to enter
        
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.strike_width_pct = strike_width_pct
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.strike_step = strike_step
        self.lot_size = lot_size
        self.iv_percentile_max = iv_percentile_max
        self.atr_period = atr_period
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        
        # Position tracking
        self.position = None  # 'SHORT_STRANGLE' when position is active
        self.entry_credit = None  # Net credit received
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details
        self.options_legs = []  # List of option legs
        self.position_id = 0
        self.call_strike = None
        self.put_strike = None
        self.max_profit = 0  # Maximum profit (credit received)
        
        # Trade log for detailed reporting
        self.trade_log = []
        
        # Underlying symbol tracking
        self.underlying_symbol = None
        self.option_expiry_date = None
        
        # IV tracking for percentile calculation
        self.iv_history = []
        
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
    
    def calculate_iv_percentile(self, historical_data):
        """
        Calculate implied volatility percentile
        Using historical volatility as proxy for IV
        """
        if len(historical_data) < 30:
            return 50  # Default to median if insufficient data
        
        # Calculate historical volatility (20-day rolling)
        returns = historical_data['close'].pct_change()
        current_hv = returns.tail(20).std() * np.sqrt(252)
        
        # Track HV history
        self.iv_history.append(current_hv)
        
        # Keep only last 252 days (1 year)
        if len(self.iv_history) > 252:
            self.iv_history = self.iv_history[-252:]
        
        # Calculate percentile
        if len(self.iv_history) < 30:
            return 50
        
        percentile = (np.sum(np.array(self.iv_history) < current_hv) / len(self.iv_history)) * 100
        
        return percentile
    
    def round_to_strike(self, price):
        """Round price to nearest strike"""
        return int(round(price / self.strike_step) * self.strike_step)
    
    def set_underlying_symbol(self, symbol):
        """Set the underlying symbol and extract expiry information"""
        self.underlying_symbol = symbol
        self.option_expiry_date = None  # Will be calculated based on entry date
    
    def get_next_expiry(self, current_date):
        """
        Get next weekly/monthly expiry (last Thursday of month or nearest weekly)
        For simplicity, using weekly expiry (every Thursday)
        """
        current_date_obj = pd.to_datetime(current_date)
        
        # Find next Thursday
        days_ahead = 3 - current_date_obj.weekday()  # Thursday = 3
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_expiry = current_date_obj + timedelta(days=days_ahead)
        
        # Ensure we have minimum and maximum DTE
        days_to_expiry = (next_expiry - current_date_obj).days
        
        if days_to_expiry < self.min_days_to_expiry:
            # Use next week's expiry
            next_expiry += timedelta(days=7)
        elif days_to_expiry > self.max_days_to_expiry:
            # Use current week if within max DTE
            pass
        
        return next_expiry
    
    def get_option_symbol(self, strike, option_type, expiry_date):
        """
        Construct option symbol name for MongoDB query
        Format: NSEFO:#NIFTYYYYYMMDDCE/PESTRIKE
        """
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
        """
        Theoretical option premium estimation (fallback)
        Using simplified Black-Scholes approximation
        """
        if days_to_expiry <= 0 or atr is None or atr == 0:
            return 0
        
        # Estimate IV from ATR
        iv_estimate = (atr / spot) * np.sqrt(252 / days_to_expiry)
        iv_estimate = max(0.1, min(1.0, iv_estimate))
        
        # Time value factor
        time_factor = np.sqrt(days_to_expiry / 365.0)
        
        if option_type == 'CE':  # Call
            moneyness = (strike - spot) / spot
            if moneyness > 0:  # OTM
                intrinsic = 0
                extrinsic = spot * iv_estimate * time_factor * np.exp(-moneyness * 2)
            else:  # ITM
                intrinsic = spot - strike
                extrinsic = spot * iv_estimate * time_factor * 0.5
        else:  # Put
            moneyness = (spot - strike) / spot
            if moneyness > 0:  # OTM
                intrinsic = 0
                extrinsic = spot * iv_estimate * time_factor * np.exp(-moneyness * 2)
            else:  # ITM
                intrinsic = strike - spot
                extrinsic = spot * iv_estimate * time_factor * 0.5
        
        premium = intrinsic + extrinsic
        return max(0, premium)
    
    def get_premium_value(self, strike, option_type, current_date, expiry_date, spot, atr):
        """
        Get option premium - try database first, fall back to estimation
        """
        # Try database first
        premium = self.fetch_option_premium(strike, option_type, current_date, expiry_date)
        
        if premium is not None and premium > 0:
            return premium
        
        # Fallback to theoretical estimation
        days_to_expiry = (pd.to_datetime(expiry_date) - pd.to_datetime(current_date)).days
        return self.estimate_premium_theoretical(spot, strike, atr, option_type, days_to_expiry)
    
    def should_enter(self, data):
        """
        Check if conditions are met to enter a short strangle
        
        SIMPLIFIED FOR TESTING - Will enter almost always
        """
        if self.position is not None:
            print(f"  → Already in position")
            return False
        
        if len(data) < self.atr_period + 30:
            return False
        
        # Check we have enough bars
        return True
    
    def build_strangle(self, current_bar, historical_data):
        """
        Build short strangle position by selling OTM call and OTM put
        
        Returns:
            dict: Position details or None if unable to build
        """
        try:
            spot = current_bar['close']
            current_date = current_bar['date']
            
            # Get expiry date
            expiry_date = self.get_next_expiry(current_date)
            days_to_expiry = (pd.to_datetime(expiry_date) - pd.to_datetime(current_date)).days
            
            if days_to_expiry < self.min_days_to_expiry or days_to_expiry > self.max_days_to_expiry:
                return None
            
            # Calculate ATR for premium estimation
            atr = self.calculate_atr(historical_data)
            if atr is None:
                return None
            
            # Calculate strike prices
            strike_width = spot * self.strike_width_pct
            
            # Call strike: above spot (OTM)
            call_strike_raw = spot + strike_width
            call_strike = self.round_to_strike(call_strike_raw)
            
            # Put strike: below spot (OTM)
            put_strike_raw = spot - strike_width
            put_strike = self.round_to_strike(put_strike_raw)
            
            # Get premiums
            call_premium = self.get_premium_value(call_strike, 'CE', current_date, 
                                                   expiry_date, spot, atr)
            put_premium = self.get_premium_value(put_strike, 'PE', current_date, 
                                                 expiry_date, spot, atr)
            
            if call_premium <= 0 or put_premium <= 0:
                return None
            
            # Net credit received (we're selling both options)
            net_credit = call_premium + put_premium
            
            # Build position details
            position = {
                'type': 'SHORT_STRANGLE',
                'entry_date': current_date,
                'expiry_date': expiry_date,
                'days_to_expiry': days_to_expiry,
                'spot': spot,
                'call_strike': call_strike,
                'put_strike': put_strike,
                'call_premium': call_premium,
                'put_premium': put_premium,
                'net_credit': net_credit,
                'lot_size': self.lot_size,
                'legs': [
                    {
                        'type': 'CE',
                        'side': 'SELL',
                        'strike': call_strike / 100,  # Convert to rupees for display
                        'premium': call_premium,
                        'entry_premium': call_premium,  # Store in paise as from DB
                        'option_type': 'CE',
                        'quantity': self.lot_size
                    },
                    {
                        'type': 'PE',
                        'side': 'SELL',
                        'strike': put_strike / 100,  # Convert to rupees for display
                        'premium': put_premium,
                        'entry_premium': put_premium,  # Store in paise as from DB
                        'option_type': 'PE',
                        'quantity': self.lot_size
                    }
                ]
            }
            
            return position
            
        except Exception as e:
            print(f"Error building strangle: {e}")
            return None
    
    def enter_position(self, current_bar, historical_data):
        """Enter a short strangle position"""
        position_details = self.build_strangle(current_bar, historical_data)
        
        if position_details is None:
            return None
        
        self.position = 'SHORT_STRANGLE'
        self.entry_date = position_details['entry_date']
        self.entry_spot = position_details['spot']
        self.entry_credit = position_details['net_credit']
        self.call_strike = position_details['call_strike']
        self.put_strike = position_details['put_strike']
        self.option_expiry_date = position_details['expiry_date']
        self.options_legs = position_details['legs']
        self.max_profit = self.entry_credit * self.lot_size  # Max profit = premium received
        self.position_id += 1
        
        # Log entry
        self.trade_log.append({
            'position_id': self.position_id,
            'action': 'ENTRY',
            'date': self.entry_date,
            'spot': self.entry_spot,
            'call_strike': self.call_strike,
            'put_strike': self.put_strike,
            'call_premium': position_details['call_premium'],
            'put_premium': position_details['put_premium'],
            'net_credit': self.entry_credit,
            'days_to_expiry': position_details['days_to_expiry']
        })
        
        # Clear console output showing entry
        print(f"\n{'='*80}")
        print(f"📍 ENTRY #{self.position_id} at {pd.to_datetime(self.entry_date).strftime('%Y-%m-%d %H:%M')}")
        print(f"   Spot: ₹{self.entry_spot/100:.2f}")
        print(f"   Call Strike: ₹{self.call_strike/100:.0f} @ ₹{position_details['call_premium']/100:.2f}")
        print(f"   Put Strike: ₹{self.put_strike/100:.0f} @ ₹{position_details['put_premium']/100:.2f}")
        print(f"   Net Credit: ₹{self.entry_credit/100:.2f} (Total: ₹{self.entry_credit*self.lot_size/100:.2f})")
        print(f"   DTE: {position_details['days_to_expiry']} days")
        print(f"{'='*80}")
        
        return 'SHORT_STRANGLE'
    
    def exit_position(self, current_bar, historical_data, reason='HOLD_DAYS'):
        """Exit short strangle position"""
        if self.position is None:
            return None
        
        current_date = current_bar['date']
        spot = current_bar['close']
        
        # Calculate current value of options
        atr = self.calculate_atr(historical_data)
        
        call_current = self.get_premium_value(self.call_strike, 'CE', current_date,
                                               self.option_expiry_date, spot, atr)
        put_current = self.get_premium_value(self.put_strike, 'PE', current_date,
                                             self.option_expiry_date, spot, atr)
        
        # Cost to close (buy back the options we sold)
        closing_cost = call_current + put_current
        
        # P&L = Credit received - Cost to close
        pnl = self.entry_credit - closing_cost
        pnl_total = pnl * self.lot_size
        pnl_pct = (pnl / self.entry_credit) if self.entry_credit > 0 else 0
        
        # Log exit
        self.trade_log.append({
            'position_id': self.position_id,
            'action': 'EXIT',
            'date': current_date,
            'exit_reason': reason,
            'spot': spot,
            'call_current': call_current,
            'put_current': put_current,
            'closing_cost': closing_cost,
            'pnl': pnl,
            'pnl_total': pnl_total,
            'pnl_pct': pnl_pct * 100,
            'legs': [
                {
                    'type': 'CE',
                    'side': 'SELL',
                    'strike': self.call_strike / 100,  # Convert to rupees
                    'entry_premium': self.options_legs[0]['entry_premium'] if self.options_legs else 0,
                    'exit_premium': call_current,
                    'quantity': self.lot_size
                },
                {
                    'type': 'PE',
                    'side': 'SELL',
                    'strike': self.put_strike / 100,  # Convert to rupees
                    'entry_premium': self.options_legs[1]['entry_premium'] if len(self.options_legs) > 1 else 0,
                    'exit_premium': put_current,
                    'quantity': self.lot_size
                }
            ]
        })
        
        # Clear console output showing exit
        print(f"\n{'='*80}")
        print(f"🏁 EXIT #{self.position_id} at {pd.to_datetime(current_date).strftime('%Y-%m-%d %H:%M')} - {reason}")
        print(f"   Spot: ₹{spot/100:.2f}")
        print(f"   Call Buyback: ₹{call_current/100:.2f} | Put Buyback: ₹{put_current/100:.2f}")
        print(f"   Closing Cost: ₹{closing_cost/100:.2f} (Total: ₹{closing_cost*self.lot_size/100:.2f})")
        print(f"   P&L: ₹{pnl_total/100:,.2f} ({pnl_pct*100:.2f}%)")
        print(f"   Days Held: {(pd.to_datetime(current_date) - pd.to_datetime(self.entry_date)).days}")
        print(f"{'='*80}\n")
        
        # Store legs before reset for backtest engine
        stored_legs = self.options_legs.copy()
        
        # Reset position
        self.position = None
        self.entry_date = None
        self.entry_credit = None
        self.entry_spot = None
        call_strike_temp = self.call_strike
        put_strike_temp = self.put_strike
        self.call_strike = None
        self.put_strike = None
        self.options_legs = stored_legs  # Keep for backtest engine display
        
        return pnl_total
    
    def should_exit(self, current_bar, historical_data):
        """
        Check if position should be exited
        
        Exit Conditions:
        1. Profit target reached (50% of max profit)
        2. Stop loss hit (200% of credit received)
        3. Hold days elapsed
        4. Near expiry (< 2 days)
        """
        if self.position is None:
            return False, None
        
        current_date = pd.to_datetime(current_bar['date'])
        days_held = (current_date - pd.to_datetime(self.entry_date)).days
        
        # Check hold days
        if days_held >= self.hold_days:
            return True, 'HOLD_DAYS'
        
        # Check days to expiry
        if self.option_expiry_date:
            days_to_expiry = (pd.to_datetime(self.option_expiry_date) - current_date).days
            if days_to_expiry <= 2:
                return True, 'NEAR_EXPIRY'
        
        # Get current option values
        spot = current_bar['close']
        atr = self.calculate_atr(historical_data)
        
        call_current = self.get_premium_value(self.call_strike, 'CE', current_date,
                                               self.option_expiry_date, spot, atr)
        put_current = self.get_premium_value(self.put_strike, 'PE', current_date,
                                             self.option_expiry_date, spot, atr)
        
        closing_cost = call_current + put_current
        current_pnl = self.entry_credit - closing_cost
        
        # Check profit target (% of max profit)
        if current_pnl >= self.entry_credit * self.profit_target_pct:
            return True, 'PROFIT_TARGET'
        
        # Check stop loss (loss exceeds % of credit received)
        if current_pnl <= -self.entry_credit * self.stop_loss_pct:
            return True, 'STOP_LOSS'
        
        return False, None
    
    def generate_signal(self, current_bar, historical_data):
        """
        Generate trading signal for short strangle (required by backtest engine)
        
        Entry Conditions:
        1. No existing position
        2. IV percentile below threshold (low volatility)
        3. Designated entry day (Thursday)
        4. Sufficient historical data
        
        Exit Conditions:
        1. Profit target reached (50% of max profit)
        2. Stop loss hit (200% of credit)
        3. Hold days elapsed
        4. Near expiry (< 2 days)
        
        Returns:
            str: 'BUY' (enter short strangle), 'SELL' (exit position), or 'HOLD'
        """
        current_price = current_bar['close']
        current_date = current_bar['date']
        
        # Initial confirmation that strategy is running - WRITE TO FILE
        if len(historical_data) == 100:
            with open('strategy_debug.log', 'w') as f:
                f.write(f"SHORT STRANGLE LOADED at bar 100, Date={current_date}\n")
                f.write(f"entry_day={self.entry_day}, iv_max={self.iv_percentile_max}\n")
            print(f"✓ SHORT STRANGLE STRATEGY LOADED - First signal at bar 100, Date={current_date}")
        
        # Log every call
        if len(historical_data) % 10000 == 0:
            with open('strategy_debug.log', 'a') as f:
                f.write(f"Bar {len(historical_data)}: generate_signal called, Date={current_date}\n")
        
        # Need sufficient data
        if len(historical_data) < self.atr_period + 30:
            return 'HOLD'
        
        # === ENTRY LOGIC ===
        if self.position is None:
            # Debug logging
            if len(historical_data) % 5000 == 0:
                print(f"DEBUG Bar {len(historical_data)}: Checking entry, Date={current_date}, IV_history_len={len(self.iv_history)}")
            
            # Check if should enter
            if self.should_enter(historical_data):
                # Attempt to build and enter position
                result = self.enter_position(current_bar, historical_data)
                if result:
                    print(f"✓ ENTRY at {current_date}, Spot=₹{current_price/100:.2f}")
                    return 'SELL_SHORT'  # Signal entry (selling options)
                else:
                    print(f"✗ Entry check passed but build_strangle failed at {current_date}")
            
            return 'HOLD'
        
        # === EXIT LOGIC ===
        else:
            # Check if should exit
            should_exit, reason = self.should_exit(current_bar, historical_data)
            if should_exit:
                pnl = self.exit_position(current_bar, historical_data, reason)
                print(f"✓ EXIT at {current_date}, Reason={reason}, PnL=₹{pnl:,.2f}")
                return 'BUY_SHORT'  # Signal exit (buying back options)
            
            return 'HOLD'
    
    def get_trade_log(self):
        """Return detailed trade log"""
        return pd.DataFrame(self.trade_log) if self.trade_log else pd.DataFrame()
