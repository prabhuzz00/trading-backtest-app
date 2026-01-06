"""
Debug why premium calculation returns 0
"""
import sys
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Simulate the strategy's premium calculation
def estimate_premium_theoretical(spot, strike, atr, option_type, days_to_expiry):
    """Theoretical option premium estimation"""
    print(f"\n  Estimating premium:")
    print(f"    Spot: {spot:.2f}")
    print(f"    Strike: {strike:.2f}")
    atr_str = f"{atr:.2f}" if atr is not None else 'None'
    print(f"    ATR: {atr_str}")
    print(f"    Type: {option_type}")
    print(f"    Days to expiry: {days_to_expiry}")
    
    if days_to_expiry <= 0 or atr is None or atr == 0:
        print(f"    -> FAILED: days_to_expiry={days_to_expiry}, atr={atr}")
        return 0
    
    iv_estimate = (atr / spot) * np.sqrt(252 / days_to_expiry)
    iv_estimate = max(0.1, min(1.0, iv_estimate))
    print(f"    IV estimate: {iv_estimate:.4f}")
    
    time_factor = np.sqrt(days_to_expiry / 365.0)
    print(f"    Time factor: {time_factor:.4f}")
    
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
    print(f"    Intrinsic: {intrinsic:.2f}")
    print(f"    Extrinsic: {extrinsic:.2f}")
    print(f"    -> Premium: {premium:.2f}")
    
    return max(0, premium)

# Test with real values
print("="*80)
print("TESTING PREMIUM CALCULATION")
print("="*80)

spot = 23500  # Nifty spot in Rupees
atr = 200  # Typical ATR for Nifty

# Test OTM Call (2% above spot)
print("\n1. OTM CALL (2% above spot)")
strike_call = spot * 1.02
premium_call = estimate_premium_theoretical(spot, strike_call, atr, 'CE', 7)

# Test OTM Put (2% below spot)  
print("\n2. OTM PUT (2% below spot)")
strike_put = spot * 0.98
premium_put = estimate_premium_theoretical(spot, strike_put, atr, 'PE', 7)

# Test with strike in paise (MongoDB format)
print("\n3. OTM CALL with strike in PAISE (incorrect)")
strike_call_paise = int(strike_call * 100)  # Convert to paise
premium_call_paise = estimate_premium_theoretical(spot, strike_call_paise, atr, 'CE', 7)

print("\n" + "="*80)
print("ISSUE FOUND:")
print("If strike is in paise but spot is in rupees, moneyness calculation fails!")
print("This makes premium = 0 or very small")
print("\nSOLUTION:")
print("Ensure both spot and strike are in same units (both Rupees or both paise)")
