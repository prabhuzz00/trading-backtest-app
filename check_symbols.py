"""
Quick script to check available symbols in the database
"""

import sys
sys.path.insert(0, r'd:\project\trading-backtest-app\src')

from utils.db_connection import get_available_stocks, get_available_options

try:
    print("Fetching available symbols from database...")
    
    # Check options
    print("\n" + "="*80)
    print("OPTIONS (NSEFO)")
    print("="*80)
    options = get_available_options()
    
    if options:
        print(f"\nFound {len(options)} option contracts")
        
        # Show NIFTY options
        nifty_options = [s for s in options if 'NIFTY' in s]
        if nifty_options:
            print(f"\nNIFTY Options ({len(nifty_options)}):")
            print("First 20 contracts:")
            for i, sym in enumerate(nifty_options[:20]):
                print(f"  {i+1}. {sym}")
            if len(nifty_options) > 20:
                print(f"  ... and {len(nifty_options) - 20} more")
                
            # Show last expiry
            print(f"\nLast 10 contracts:")
            for i, sym in enumerate(nifty_options[-10:]):
                print(f"  {i+1}. {sym}")
    else:
        print("No options found in database")
    
    # Check stocks
    print("\n" + "="*80)
    print("STOCKS (EQ)")
    print("="*80)
    symbols = get_available_stocks()
    
    if symbols:
        print(f"\nFound {len(symbols)} stock symbols (showing first 10):")
        for i, sym in enumerate(symbols[:10]):
            print(f"  {i+1}. {sym}")
    else:
        print("No symbols found in database")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
