"""
Test script for Lightweight Chart functionality
Run this to verify the chart component works independently
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate
import sys
import pandas as pd
from datetime import datetime, timedelta

# Import the chart widget
from src.ui.lightweight_ohlc_chart import LightweightOHLCChart

def generate_test_data(days=100):
    """Generate sample OHLC data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate realistic price data
    import numpy as np
    np.random.seed(42)
    
    close_prices = 100 + np.cumsum(np.random.randn(days) * 2)
    
    data = pd.DataFrame({
        'date': dates,
        'open': close_prices + np.random.randn(days) * 0.5,
        'high': close_prices + np.abs(np.random.randn(days) * 1.5),
        'low': close_prices - np.abs(np.random.randn(days) * 1.5),
        'close': close_prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })
    
    return data

def generate_test_trades(data):
    """Generate sample trades"""
    trades = []
    for i in range(0, len(data), 20):
        if i < len(data):
            trades.append({
                'date': data.iloc[i]['date'],
                'action': 'BUY',
                'price': float(data.iloc[i]['close']),
                'quantity': 100
            })
        if i + 10 < len(data):
            trades.append({
                'date': data.iloc[i+10]['date'],
                'action': 'SELL',
                'price': float(data.iloc[i+10]['close']),
                'quantity': 100
            })
    return trades

def main():
    print("\n" + "="*60)
    print("LIGHTWEIGHT CHART TEST")
    print("="*60 + "\n")
    
    # Check imports
    print("1. Checking imports...")
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        print("   ✓ PyQt6-WebEngine available")
    except ImportError as e:
        print(f"   ✗ PyQt6-WebEngine NOT available: {e}")
        return
    
    # Create application
    print("\n2. Creating Qt Application...")
    app = QApplication(sys.argv)
    print("   ✓ Application created")
    
    # Create chart widget
    print("\n3. Creating chart widget...")
    chart = LightweightOHLCChart()
    chart.setWindowTitle("Lightweight Chart Test")
    chart.resize(1200, 800)
    print("   ✓ Chart widget created")
    
    # Generate test data
    print("\n4. Generating test data...")
    price_data = generate_test_data(100)
    trades = generate_test_trades(price_data)
    print(f"   ✓ Generated {len(price_data)} candles")
    print(f"   ✓ Generated {len(trades)} trades")
    
    # Plot data
    print("\n5. Plotting data...")
    chart.plot_ohlc_with_trades(price_data, trades)
    print("   ✓ Plot method called")
    
    # Show window
    print("\n6. Displaying window...")
    chart.show()
    print("   ✓ Window displayed")
    
    print("\n" + "="*60)
    print("If you see a chart with candlesticks and trade markers,")
    print("the lightweight chart is working correctly!")
    print("\nIf you see an error message in the chart:")
    print("- Check your internet connection (CDN required)")
    print("- Look at the console output above for details")
    print("="*60 + "\n")
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
