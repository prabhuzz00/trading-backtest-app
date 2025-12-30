"""
NIFTY Options Straddle Strategy with Strike & Side Tracking

This strategy simulates options trading (long straddle or iron condor) on NIFTY
by tracking which strikes and option types (CE/PE) would be traded.

Strategy Logic:
- Entry: Monday (or specified day) when volatility conditions are met
- Position: Long Straddle (buy ATM call + ATM put) or Iron Condor
- Exit: End of week OR profit/stop targets hit
- Tracking: Records exact strikes, premiums, and CE/PE positions

Parameters:
    - strategy_type: 'LONG_STRADDLE' or 'IRON_CONDOR' (default: 'LONG_STRADDLE')
    - entry_day: Day to enter (0=Monday, 4=Friday) (default: 0)
    - hold_days: Days to hold (default: 4)
    - atr_period: ATR calculation period (default: 14)
    - volatility_threshold: Min vol ratio for entry (default: 1.2)
    - profit_target_pct: Exit profit % (default: 0.50 = 50%)
    - stop_loss_pct: Exit loss % (default: 0.75 = 75%)
    - strike_step: NIFTY strike step (default: 50)
    - lot_size: NIFTY lot size (default: 50)
"""

import pandas as pd
import numpy as np
from datetime import datetime

class Strategy:
    """
    NIFTY Options Strategy with detailed strike and side tracking
    """
    
    def __init__(self, 
                 strategy_type='LONG_STRADDLE',
                 entry_day=0, 
                 hold_days=4,
                 atr_period=14,
                 volatility_threshold=1.2,
                 profit_target_pct=0.50,
                 stop_loss_pct=0.75,
                 strike_step=50,
                 lot_size=50):
        
        self.strategy_type = strategy_type
        self.entry_day = entry_day
        self.hold_days = hold_days
        self.atr_period = atr_period
        self.volatility_threshold = volatility_threshold
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.strike_step = strike_step
        self.lot_size = lot_size
        
        # Position tracking
        self.position = None  # Current position
        self.entry_price = None
        self.entry_date = None
        self.entry_spot = None
        
        # Options position details (for tracking)
        self.options_legs = []  # List of dict: {strike, type: 'CE'/'PE', side: 'BUY'/'SELL', premium}
        self.position_id = 0
        
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
    
    def round_to_strike(self, price):
        """Round price to nearest strike"""
        return int(round(price / self.strike_step) * self.strike_step)
    
    def estimate_option_premium(self, spot, strike, atr, option_type, days_to_expiry):
        """
        Estimate option premium based on ATR and moneyness
        This is a simplified model for simulation purposes
        """
        # Base premium from ATR
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
    
    def build_long_straddle(self, spot, atr, days_to_expiry):
        """Build long straddle position (buy ATM call + put)"""
        atm_strike = self.round_to_strike(spot)
        
        # Estimate premiums
        ce_premium = self.estimate_option_premium(spot, atm_strike, atr, 'CE', days_to_expiry)
        pe_premium = self.estimate_option_premium(spot, atm_strike, atr, 'PE', days_to_expiry)
        
        legs = [
            {'strike': atm_strike, 'type': 'CE', 'side': 'BUY', 'entry_premium': ce_premium},
            {'strike': atm_strike, 'type': 'PE', 'side': 'BUY', 'entry_premium': pe_premium}
        ]
        
        # Total cost (debit paid)
        total_cost = ce_premium + pe_premium
        
        return legs, -total_cost  # Negative because we pay
    
    def build_iron_condor(self, spot, atr, days_to_expiry):
        """Build iron condor position (sell OTM call/put, buy further OTM for protection)"""
        atm_strike = self.round_to_strike(spot)
        
        # Iron condor strikes (wider spreads)
        short_call_strike = atm_strike + int(1.5 * atr / self.strike_step) * self.strike_step
        long_call_strike = short_call_strike + 2 * self.strike_step
        short_put_strike = atm_strike - int(1.5 * atr / self.strike_step) * self.strike_step
        long_put_strike = short_put_strike - 2 * self.strike_step
        
        # Estimate premiums
        sc_premium = self.estimate_option_premium(spot, short_call_strike, atr, 'CE', days_to_expiry)
        lc_premium = self.estimate_option_premium(spot, long_call_strike, atr, 'CE', days_to_expiry)
        sp_premium = self.estimate_option_premium(spot, short_put_strike, atr, 'PE', days_to_expiry)
        lp_premium = self.estimate_option_premium(spot, long_put_strike, atr, 'PE', days_to_expiry)
        
        legs = [
            {'strike': short_call_strike, 'type': 'CE', 'side': 'SELL', 'entry_premium': sc_premium},
            {'strike': long_call_strike, 'type': 'CE', 'side': 'BUY', 'entry_premium': lc_premium},
            {'strike': short_put_strike, 'type': 'PE', 'side': 'SELL', 'entry_premium': sp_premium},
            {'strike': long_put_strike, 'type': 'PE', 'side': 'BUY', 'entry_premium': lp_premium}
        ]
        
        # Net credit received
        net_credit = (sc_premium + sp_premium) - (lc_premium + lp_premium)
        
        return legs, net_credit  # Positive because we receive credit
    
    def calculate_position_value(self, legs, current_spot, current_atr, days_remaining):
        """Calculate current value of options position"""
        total_value = 0
        
        for leg in legs:
            current_premium = self.estimate_option_premium(
                current_spot, leg['strike'], current_atr, leg['type'], days_remaining
            )
            
            if leg['side'] == 'BUY':
                total_value += current_premium
            else:  # SELL
                total_value -= current_premium
        
        return total_value
    
    def get_weekday(self, date_val):
        """Get day of week (0=Monday)"""
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
        
        info = f"\n{'='*60}\n"
        info += f"Position ID: {self.position_id} | Strategy: {self.strategy_type}\n"
        info += f"Entry Date: {self.entry_date} | Spot: {self.entry_spot:.2f}\n"
        info += f"{'='*60}\n"
        info += f"{'Strike':<10} {'Type':<6} {'Side':<6} {'Premium':<12}\n"
        info += f"{'-'*60}\n"
        
        for leg in self.options_legs:
            info += f"{leg['strike']:<10} {leg['type']:<6} {leg['side']:<6} {leg['entry_premium']:<12.2f}\n"
        
        info += f"{'='*60}\n"
        return info
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal with options tracking"""
        current_price = current_bar['close']
        current_date = current_bar['date']
        weekday = self.get_weekday(current_date)
        
        if len(historical_data) < self.atr_period * 3:
            return 'HOLD'
        
        vol_ratio = self.calculate_volatility_ratio(historical_data)
        current_atr = self.calculate_atr(historical_data)
        
        if vol_ratio is None or current_atr is None:
            return 'HOLD'
        
        # Exit logic
        if self.position is not None:
            days_held = self.days_since_entry(current_date)
            days_remaining = max(0, self.hold_days - days_held)
            
            # Calculate current position value
            current_value = self.calculate_position_value(
                self.options_legs, current_price, current_atr, days_remaining
            )
            
            # P&L calculation
            pnl = current_value - self.entry_price
            pnl_pct = (pnl / abs(self.entry_price)) if self.entry_price != 0 else 0
            
            # Exit conditions
            should_exit = False
            exit_reason = ""
            
            if pnl_pct >= self.profit_target_pct:
                should_exit = True
                exit_reason = f"Profit target hit: {pnl_pct:.1%}"
            elif pnl_pct <= -self.stop_loss_pct:
                should_exit = True
                exit_reason = f"Stop loss hit: {pnl_pct:.1%}"
            elif days_held >= self.hold_days:
                should_exit = True
                exit_reason = f"Hold period ended ({days_held} days)"
            
            if should_exit:
                # Log exit details
                exit_info = {
                    'position_id': self.position_id,
                    'exit_date': current_date,
                    'exit_spot': current_price,
                    'entry_spot': self.entry_spot,
                    'days_held': days_held,
                    'entry_value': self.entry_price,
                    'exit_value': current_value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': exit_reason,
                    'legs': self.options_legs.copy()
                }
                self.trade_log.append(exit_info)
                
                # Print detailed exit info
                print(f"\n{'='*70}")
                print(f"CLOSING POSITION {self.position_id}")
                print(f"Exit Reason: {exit_reason}")
                print(f"Entry: {self.entry_date} @ Spot {self.entry_spot:.2f}")
                print(f"Exit:  {current_date} @ Spot {current_price:.2f}")
                print(f"Days Held: {days_held}")
                print(f"P&L: ₹{pnl * self.lot_size:,.2f} ({pnl_pct:+.2%})")
                print(f"{'='*70}\n")
                
                # Reset position
                self.position = None
                self.entry_price = None
                self.entry_date = None
                self.options_legs = []
                
                return 'SELL_LONG' if exit_info['pnl'] >= 0 else 'SELL_LONG'
        
        # Entry logic - only on specified weekday
        if weekday == self.entry_day and self.position is None:
            should_enter = False
            
            if self.strategy_type == 'LONG_STRADDLE':
                # Enter long straddle when volatility is high
                if vol_ratio >= self.volatility_threshold:
                    should_enter = True
            elif self.strategy_type == 'IRON_CONDOR':
                # Enter iron condor when volatility is moderate/low
                if vol_ratio < self.volatility_threshold:
                    should_enter = True
            
            if should_enter:
                days_to_expiry = self.hold_days
                
                # Build position
                if self.strategy_type == 'LONG_STRADDLE':
                    legs, entry_cost = self.build_long_straddle(current_price, current_atr, days_to_expiry)
                else:
                    legs, entry_cost = self.build_iron_condor(current_price, current_atr, days_to_expiry)
                
                self.position = 'LONG'
                self.entry_price = entry_cost
                self.entry_date = current_date
                self.entry_spot = current_price
                self.options_legs = legs
                self.position_id += 1
                
                # Print detailed entry info
                print(self.format_position_info())
                print(f"Net {'Debit' if entry_cost < 0 else 'Credit'}: ₹{abs(entry_cost * self.lot_size):,.2f}")
                print(f"Volatility Ratio: {vol_ratio:.2f}")
                print(f"ATR: {current_atr:.2f}\n")
                
                return 'BUY_LONG'
        
        return 'HOLD'
    
    def get_trade_summary(self):
        """Get summary of all trades executed"""
        if not self.trade_log:
            return "No trades executed yet."
        
        summary = f"\n{'='*80}\n"
        summary += f"OPTIONS TRADING SUMMARY - {self.strategy_type}\n"
        summary += f"{'='*80}\n\n"
        
        total_pnl = sum(t['pnl'] * self.lot_size for t in self.trade_log)
        winning_trades = [t for t in self.trade_log if t['pnl'] > 0]
        losing_trades = [t for t in self.trade_log if t['pnl'] < 0]
        
        summary += f"Total Trades: {len(self.trade_log)}\n"
        summary += f"Winning Trades: {len(winning_trades)} ({len(winning_trades)/len(self.trade_log)*100:.1f}%)\n"
        summary += f"Losing Trades: {len(losing_trades)} ({len(losing_trades)/len(self.trade_log)*100:.1f}%)\n"
        summary += f"Total P&L: ₹{total_pnl:,.2f}\n"
        summary += f"Avg P&L per Trade: ₹{total_pnl/len(self.trade_log):,.2f}\n\n"
        
        summary += f"{'ID':<6} {'Entry Date':<12} {'Exit Date':<12} {'Days':<6} {'P&L':<15} {'P&L %':<10} {'Reason':<30}\n"
        summary += f"{'-'*80}\n"
        
        for trade in self.trade_log:
            pnl_rupees = trade['pnl'] * self.lot_size
            summary += f"{trade['position_id']:<6} "
            summary += f"{str(trade['entry_date'])[:10]:<12} "
            summary += f"{str(trade['exit_date'])[:10]:<12} "
            summary += f"{trade['days_held']:<6} "
            summary += f"₹{pnl_rupees:>12,.2f} "
            summary += f"{trade['pnl_pct']:>8.2%} "
            summary += f"{trade['exit_reason']}\n"
        
        summary += f"{'='*80}\n"
        return summary
