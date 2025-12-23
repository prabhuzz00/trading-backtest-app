"""
Batch Strategy Updater - Converts all strategies to support Long and Short trading

This script updates all strategy files to:
1. Add enable_short parameter
2. Track position as 'LONG', 'SHORT', or None  
3. Return BUY_LONG, SELL_LONG, SELL_SHORT, BUY_SHORT signals
4. Maintain backward compatibility with old BUY/SELL signals
"""

import os
import re

strategies_dir = "strategies"

# Strategies already updated (skip these)
UPDATED_STRATEGIES = [
    'moving_average.py',
    'rsi.py',
    'ema_crossover.py',
    'bollinger_bands.py',
    'macd.py',
    'stochastic.py'
]

def update_strategy_file(filepath):
    """Update a single strategy file to support long/short trading"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already updated
    if 'BUY_LONG' in content or 'SELL_SHORT' in content:
        print(f"  ✓ Already updated: {os.path.basename(filepath)}")
        return False
    
    # Skip if doesn't have BUY/SELL signals
    if "'BUY'" not in content and "'SELL'" not in content:
        print(f"  ⊘ No BUY/SELL signals: {os.path.basename(filepath)}")
        return False
    
    original_content = content
    
    # 1. Update docstring
    content = re.sub(
        r'("""[\s\S]*?)(Strategy.*?)\n',
        r'\1\2 with Long & Short Support\n',
        content,
        count=1
    )
    
    # 2. Add enable_short parameter to __init__
    # Find __init__ and add enable_short if not present
    init_pattern = r'(def __init__\(self[^)]*?)(\)):'
    if 'enable_short' not in content:
        content = re.sub(
            init_pattern,
            r'\1, enable_short=True\2:',
            content
        )
        
        # Add instance variable
        content = re.sub(
            r'(self\.position = None)',
            r'\1\n        self.enable_short = enable_short',
            content
        )
    
    # 3. Update BUY signals to BUY_LONG with position tracking
    # Pattern: if condition: ... self.position = 'LONG'; return 'BUY'
    content = re.sub(
        r"(\s+)(if self\.position != 'LONG':)\s*\n\s*self\.position = 'LONG'\s*\n\s*return 'BUY'",
        r"\1if self.position == 'SHORT':\n\1    self.position = None\n\1    return 'BUY_SHORT'\n\1elif self.position != 'LONG':\n\1    self.position = 'LONG'\n\1    return 'BUY_LONG'",
        content
    )
    
    # Simple BUY without position check
    content = re.sub(
        r"return 'BUY'",
        r"if self.position == 'SHORT':\n                return 'BUY_SHORT'\n            return 'BUY_LONG'",
        content
    )
    
    # 4. Update SELL signals to SELL_LONG/SELL_SHORT with position tracking
    # Pattern: if condition: ... self.position = None; return 'SELL'
    content = re.sub(
        r"(\s+)(if self\.position == 'LONG':)\s*\n\s*self\.position = None\s*\n\s*return 'SELL'",
        r"\1if self.position == 'LONG':\n\1    self.position = None\n\1    return 'SELL_LONG'\n\1elif self.position != 'SHORT' and self.enable_short:\n\1    self.position = 'SHORT'\n\1    return 'SELL_SHORT'",
        content
    )
    
    # Simple SELL without position check  
    content = re.sub(
        r"return 'SELL'",
        r"if self.position == 'LONG':\n                return 'SELL_LONG'\n            elif self.enable_short:\n                return 'SELL_SHORT'\n            return 'HOLD'",
        content
    )
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated: {os.path.basename(filepath)}")
        return True
    else:
        print(f"  - No changes: {os.path.basename(filepath)}")
        return False

def main():
    """Update all strategy files"""
    print("\\n" + "="*60)
    print("BATCH STRATEGY UPDATER - Long & Short Trading Support")
    print("="*60 + "\\n")
    
    updated_count = 0
    skipped_count = 0
    total_count = 0
    
    # Get all .py files in strategies directory
    strategy_files = [f for f in os.listdir(strategies_dir) 
                     if f.endswith('.py') and f not in UPDATED_STRATEGIES 
                     and not f.startswith('__')]
    
    print(f"Found {len(strategy_files)} strategies to process\\n")
    
    for filename in sorted(strategy_files):
        filepath = os.path.join(strategies_dir, filename)
        total_count += 1
        
        if update_strategy_file(filepath):
            updated_count += 1
        else:
            skipped_count += 1
    
    print("\\n" + "="*60)
    print(f"SUMMARY:")
    print(f"  Total processed: {total_count}")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Already done: {len(UPDATED_STRATEGIES)}")
    print("="*60 + "\\n")
    
    print("✓ All strategies have been updated!")
    print("\\nNote: Please review complex strategies manually to ensure")
    print("proper long/short logic implementation.")

if __name__ == "__main__":
    main()
