"""
Test real options data integration in backtest engine
"""
import sys
sys.path.append('src')

from engine.options_backtest_engine import OptionsBacktestEngine
from datetime import datetime, timedelta
import pandas as pd

def test_real_options_data():
    """Test that engine can find and use real options data"""
    
    print("\n" + "="*80)
    print("Testing Real Options Data Integration")
    print("="*80)
    
    engine = OptionsBacktestEngine(initial_cash=100000)
    
    # Test 1: Get available expiries
    print("\n1. Testing available expiries...")
    expiries = engine._get_available_expiries()
    print(f"   Found {len(expiries)} expiry dates")
    
    if expiries:
        sorted_expiries = sorted(expiries.keys())
        print(f"   First expiry: {sorted_expiries[0].strftime('%Y-%m-%d')}")
        print(f"   Last expiry: {sorted_expiries[-1].strftime('%Y-%m-%d')}")
        print(f"   Sample expiries:")
        for exp in sorted_expiries[:5]:
            count = len(expiries[exp])
            print(f"     {exp.strftime('%Y-%m-%d')}: {count} options")
    
    # Test 2: Get closest expiry
    print("\n2. Testing closest expiry finder...")
    test_date = datetime(2023, 1, 15)
    closest = engine._get_closest_expiry(test_date, min_days=7)
    if closest:
        print(f"   For date {test_date.strftime('%Y-%m-%d')}, closest expiry: {closest.strftime('%Y-%m-%d')}")
        days_diff = (closest - test_date).days
        print(f"   Days to expiry: {days_diff}")
    else:
        print(f"   No expiry found for {test_date.strftime('%Y-%m-%d')}")
    
    # Test 3: Get available strikes
    if closest:
        print("\n3. Testing available strikes...")
        ce_strikes = engine._get_available_strikes(closest, 'CE')
        pe_strikes = engine._get_available_strikes(closest, 'PE')
        
        print(f"   CE strikes: {len(ce_strikes)}")
        if ce_strikes:
            print(f"     Range: ₹{min(ce_strikes):,.0f} - ₹{max(ce_strikes):,.0f}")
            print(f"     Sample: {[f'₹{s:,.0f}' for s in ce_strikes[:5]]}")
        
        print(f"   PE strikes: {len(pe_strikes)}")
        if pe_strikes:
            print(f"     Range: ₹{min(pe_strikes):,.0f} - ₹{max(pe_strikes):,.0f}")
            print(f"     Sample: {[f'₹{s:,.0f}' for s in pe_strikes[:5]]}")
        
        # Test 4: Find ATM/OTM/ITM strikes
        if ce_strikes:
            print("\n4. Testing strike finders...")
            spot_price = 18000.0  # Example spot
            print(f"   Spot price: ₹{spot_price:,.0f}")
            
            atm = engine._find_atm_strike(spot_price, ce_strikes)
            print(f"   ATM strike: ₹{atm:,.0f}")
            
            otm_call = engine._find_otm_call_strike(spot_price, ce_strikes, otm_pct=0.02)
            print(f"   OTM Call (+2%): ₹{otm_call:,.0f}")
            
            itm_call = engine._find_itm_call_strike(spot_price, ce_strikes, itm_pct=0.02)
            print(f"   ITM Call (-2%): ₹{itm_call:,.0f}")
            
            otm_put = engine._find_otm_put_strike(spot_price, pe_strikes, otm_pct=0.02)
            print(f"   OTM Put (-2%): ₹{otm_put:,.0f}")
            
            itm_put = engine._find_itm_put_strike(spot_price, pe_strikes, itm_pct=0.02)
            print(f"   ITM Put (+2%): ₹{itm_put:,.0f}")
            
            # Test 5: Fetch real premium
            print("\n5. Testing real premium fetch...")
            test_strike = atm
            test_date = datetime(2023, 1, 15)
            
            premium = engine._fetch_option_premium(test_strike, 'CE', test_date, closest)
            if premium:
                print(f"   ✓ Found real premium for ₹{test_strike:,.0f} CE: ₹{premium:,.2f}")
            else:
                print(f"   ✗ No premium data for ₹{test_strike:,.0f} CE on {test_date.strftime('%Y-%m-%d')}")
                
                # Try a date within the expiry range
                test_date2 = closest - timedelta(days=30)
                premium2 = engine._fetch_option_premium(test_strike, 'CE', test_date2, closest)
                if premium2:
                    print(f"   ✓ Found premium for {test_date2.strftime('%Y-%m-%d')}: ₹{premium2:,.2f}")
                else:
                    print(f"   ✗ No premium data for {test_date2.strftime('%Y-%m-%d')} either")
    
    print("\n" + "="*80)
    print("Test Complete")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_real_options_data()
