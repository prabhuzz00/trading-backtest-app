"""
Event-Driven Arbitrage Strategy

This strategy attempts to profit from price discrepancies around corporate events.
Simplified version focusing on volatility and price gaps as event proxies.
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Event-Driven Arbitrage Strategy (Simplified)
    
    Parameters:
        gap_threshold: Minimum gap size to be considered an event (default: 3.0%)
        volatility_threshold: Volatility threshold for event detection (default: 2.0)
        reversion_period: Expected reversion period (default: 5)
        volume_confirmation: Require volume confirmation (default: True)
    """
    
    def __init__(self, gap_threshold=3.0, volatility_threshold=2.0, 
                 reversion_period=5, volume_confirmation=True):
        self.gap_threshold = gap_threshold
        self.volatility_threshold = volatility_threshold
        self.reversion_period = reversion_period
        self.volume_confirmation = volume_confirmation
        self.position = None
        self.event_detected = False
        self.event_price = None
        self.event_direction = None
        self.days_since_event = 0
    
    def detect_price_gap(self, prev_close, current_open, current_close):
        """Detect significant price gaps"""
        if prev_close == 0:
            return False, 0, None
        
        # Calculate gap size
        gap = (current_open - prev_close) / prev_close * 100
        
        # Significant gap detection
        if abs(gap) >= self.gap_threshold:
            gap_direction = 'up' if gap > 0 else 'down'
            return True, abs(gap), gap_direction
        
        return False, abs(gap), None
    
    def detect_volatility_spike(self, highs, lows, closes, volumes=None):
        """Detect unusual volatility spikes"""
        if len(closes) < 20:
            return False, 0
        
        # Calculate current volatility
        current_range = highs[-1] - lows[-1]
        if closes[-1] != 0:
            current_vol = current_range / closes[-1] * 100
        else:
            current_vol = 0
        
        # Calculate historical average volatility
        historical_vols = []
        for i in range(1, min(20, len(closes))):
            day_range = highs[-i] - lows[-i]
            if closes[-i] != 0:
                day_vol = day_range / closes[-i] * 100
                historical_vols.append(day_vol)
        
        if not historical_vols:
            return False, current_vol
        
        avg_vol = np.mean(historical_vols)
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
        
        # Volume confirmation if available
        volume_spike = True
        if self.volume_confirmation and volumes is not None and len(volumes) >= 10:
            current_volume = volumes[-1]
            avg_volume = np.mean(volumes[-10:-1])
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                volume_spike = volume_ratio >= 1.5  # 50% above average
        
        # Volatility spike detection
        is_spike = vol_ratio >= self.volatility_threshold and volume_spike
        
        return is_spike, current_vol
    
    def detect_event(self, current_bar, historical_data):
        """Detect potential arbitrage events"""
        if len(historical_data) < 2:
            return False, None, None
        
        # Get previous bar data
        prev_data = historical_data.iloc[-1]
        prev_close = prev_data['close']
        
        # Current bar data
        current_open = current_bar['open']
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        # Check for price gaps
        has_gap, gap_size, gap_direction = self.detect_price_gap(
            prev_close, current_open, current_close)
        
        # Check for volatility spikes
        highs = historical_data['high'].values
        lows = historical_data['low'].values
        closes = historical_data['close'].values
        
        # Include volume if available
        volumes = None
        if 'volume' in historical_data.columns:
            volumes = historical_data['volume'].values
        
        has_vol_spike, vol_level = self.detect_volatility_spike(
            np.append(highs, current_high),
            np.append(lows, current_low),
            np.append(closes, current_close),
            volumes
        )
        
        # Event detection logic
        event_type = None
        event_strength = 0
        
        if has_gap and gap_size >= self.gap_threshold:
            event_type = f'gap_{gap_direction}'
            event_strength = gap_size
        elif has_vol_spike:
            event_type = 'volatility_spike'
            event_strength = vol_level
        
        return event_type is not None, event_type, event_strength
    
    def generate_signal(self, current_bar, historical_data):
        """Generate event-driven arbitrage signals"""
        if len(historical_data) < 20:
            return 'HOLD'
        
        current_close = current_bar['close']
        
        # Detect events
        has_event, event_type, event_strength = self.detect_event(current_bar, historical_data)
        
        # Handle new events
        if has_event and not self.event_detected:
            self.event_detected = True
            self.event_price = current_close
            self.event_direction = event_type
            self.days_since_event = 0
            
            # Determine trading direction based on event type
            if 'gap_up' in event_type:
                # Expect gap fill (reversion down)
                if self.position == 'LONG':
                    self.position = None
                    return 'SELL'
            
            elif 'gap_down' in event_type:
                # Expect gap fill (reversion up)
                if self.position != 'LONG':
                    self.position = 'LONG'
                    return 'BUY'
            
            elif 'volatility_spike' in event_type:
                # Expect volatility normalization
                # Take contrarian position based on recent price movement
                if len(historical_data) >= 2:
                    recent_return = (current_close - historical_data['close'].iloc[-2]) / historical_data['close'].iloc[-2]
                    
                    if recent_return > 0:
                        # Recent move up, expect reversion down
                        if self.position == 'LONG':
                            self.position = None
                            return 'SELL'
                    else:
                        # Recent move down, expect reversion up
                        if self.position != 'LONG':
                            self.position = 'LONG'
                            return 'BUY'
        
        # Handle existing event positions
        elif self.event_detected:
            self.days_since_event += 1
            
            # Check for reversion completion or timeout
            reversion_threshold = 0.5  # 50% reversion
            
            if self.event_price and self.event_price != 0:
                price_change = (current_close - self.event_price) / self.event_price
                
                # Exit conditions
                exit_position = False
                
                # Time-based exit
                if self.days_since_event >= self.reversion_period:
                    exit_position = True
                
                # Reversion-based exit
                if 'gap_up' in str(self.event_direction) and price_change <= -reversion_threshold / 100:
                    exit_position = True
                elif 'gap_down' in str(self.event_direction) and price_change >= reversion_threshold / 100:
                    exit_position = True
                
                if exit_position and self.position == 'LONG':
                    self.position = None
                    self.event_detected = False
                    return 'SELL'
        
        return 'HOLD'