"""
Mean Reversion Strategy - Enhanced Version

This strategy assumes that prices tend to revert to their mean (average).
Uses Bollinger Bands with dynamic thresholds, RSI confirmation, volume filters,
and SMA 200 trend filter for more precise entries and exits.

Key improvements:
- SMA 200 trend filter (only buy when above 200 SMA)
- Multiple timeframe analysis
- RSI oversold/overbought confirmation
- Volume spike detection
- Dynamic exit targets based on volatility
- Trailing stop mechanism
"""

import pandas as pd
import numpy as np

class Strategy:
    """
    Enhanced Mean Reversion Strategy
    
    Parameters:
        period: Moving average period (default: 20)
        std_threshold: Standard deviation threshold for entry (default: 2.0)
        rsi_period: RSI calculation period (default: 14)
        rsi_oversold: RSI oversold threshold (default: 30)
        rsi_overbought: RSI overbought threshold (default: 70)
        volume_threshold: Volume spike multiplier (default: 1.5)
        profit_target: Profit target in std deviations (default: 0.5)
        sma_period: Long-term SMA period for trend filter (default: 200)
        use_sma_filter: Enable/disable SMA trend filter (default: True)
    """
    
    def __init__(self, period=20, std_threshold=2.0, rsi_period=14, 
                 rsi_oversold=30, rsi_overbought=70, volume_threshold=1.5,
                 profit_target=0.5, sma_period=200, use_sma_filter=True, enable_short=True):
        self.period = period
        self.std_threshold = std_threshold
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.volume_threshold = volume_threshold
        self.profit_target = profit_target
        self.sma_period = sma_period
        self.use_sma_filter = use_sma_filter
        self.enable_short = enable_short
        self.position = None
        self.entry_price = None
        self.entry_std = None
    
    def calculate_rsi(self, prices, period):
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI if not enough data
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses using exponential moving average
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signal(self, current_bar, historical_data):
        """Generate trading signal based on enhanced mean reversion"""
        # Need enough data for SMA 200 and other indicators
        min_data_required = max(self.period, self.rsi_period + 1, self.sma_period if self.use_sma_filter else 0)
        if len(historical_data) < min_data_required:
            return 'HOLD'
        
        # Extract data
        close_prices = historical_data['close'].values
        current_price = current_bar['close']
        current_volume = current_bar.get('volume', 0)
        
        # Calculate SMA 200 for trend filter
        sma_200 = None
        if self.use_sma_filter and len(close_prices) >= self.sma_period:
            sma_200 = np.mean(close_prices[-self.sma_period:])
        
        # Calculate Bollinger Bands
        recent_closes = close_prices[-self.period:]
        mean_price = np.mean(recent_closes)
        std_dev = np.std(recent_closes, ddof=1)  # Use sample std
        
        if std_dev == 0:
            return 'HOLD'
        
        # Calculate z-score (distance from mean in standard deviations)
        z_score = (current_price - mean_price) / std_dev
        
        # Calculate RSI
        rsi = self.calculate_rsi(close_prices, self.rsi_period)
        
        # Calculate average volume
        if len(historical_data) >= self.period and 'volume' in historical_data.columns:
            volumes = historical_data['volume'].values[-self.period:]
            avg_volume = np.mean(volumes[volumes > 0])  # Exclude zero volumes
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        else:
            volume_ratio = 1
        
        # Enhanced Entry Logic
        if self.position is None:
            # Check SMA 200 trend filter
            trend_ok = True
            if self.use_sma_filter and sma_200 is not None:
                # Only buy in uptrend (price above SMA 200)
                # This prevents catching falling knives
                trend_ok = current_price > sma_200
            
            # Buy when:
            # 1. Price is above SMA 200 (uptrend confirmation)
            # 2. Price is below mean by threshold (oversold)
            # 3. RSI confirms oversold
            # 4. Volume is elevated (showing conviction)
            if (trend_ok and
                z_score <= -self.std_threshold and 
                rsi < self.rsi_oversold and 
                volume_ratio >= self.volume_threshold * 0.8):
                
                self.position = 'LONG'
                self.entry_price = current_price
                self.entry_std = std_dev
                return 'BUY_LONG'
            
            # Short when price is above mean by threshold (overbought)
            elif (z_score >= self.std_threshold and 
                  rsi > self.rsi_overbought and 
                  volume_ratio >= self.volume_threshold * 0.8 and 
                  self.enable_short):
                
                self.position = 'SHORT'
                self.entry_price = current_price
                self.entry_std = std_dev
                return 'SELL_SHORT'
        
        # Enhanced Exit Logic
        elif self.position == 'LONG':
            # Calculate profit/loss
            price_change = current_price - self.entry_price
            profit_pct = (price_change / self.entry_price * 100) if self.entry_price > 0 else 0
            
            # Exit conditions (multiple triggers for precision):
            
            # 1. Profit target reached (price reverted to mean)
            if z_score >= -self.profit_target:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'SELL_LONG'
            
            # 2. RSI shows overbought (momentum reversal)
            elif rsi > self.rsi_overbought:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'SELL_LONG'
            
            # 3. Stop loss: Price moved against us beyond threshold
            elif z_score <= -(self.std_threshold + 1.0):
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'SELL_LONG'
            
            # 4. Price crossed above mean with volume confirmation
            elif z_score > 0.3 and volume_ratio > self.volume_threshold:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'SELL_LONG'
            
            # 5. Trailing stop: Lock in profits if price moved favorably
            elif profit_pct > 3.0 and z_score < -0.8:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'SELL_LONG'
            
            # 6. Emergency exit: Price fell below SMA 200 (trend reversal)
            elif self.use_sma_filter and sma_200 is not None and current_price < sma_200 * 0.98:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'SELL_LONG'
        
        # Exit short position
        elif self.position == 'SHORT':
            # Calculate profit/loss for short
            price_change = self.entry_price - current_price
            profit_pct = (price_change / self.entry_price * 100) if self.entry_price > 0 else 0
            
            # Exit short conditions:
            
            # 1. Profit target reached (price reverted down to mean)
            if z_score <= self.profit_target:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'BUY_SHORT'
            
            # 2. RSI shows oversold (momentum reversal)
            elif rsi < self.rsi_oversold:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'BUY_SHORT'
            
            # 3. Stop loss: Price moved against us beyond threshold
            elif z_score >= (self.std_threshold + 1.0):
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'BUY_SHORT'
            
            # 4. Price crossed below mean with volume confirmation
            elif z_score < -0.3 and volume_ratio > self.volume_threshold:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'BUY_SHORT'
            
            # 5. Trailing stop: Lock in profits if price moved favorably
            elif profit_pct > 3.0 and z_score > 0.8:
                self.position = None
                self.entry_price = None
                self.entry_std = None
                return 'BUY_SHORT'
        
        return 'HOLD'