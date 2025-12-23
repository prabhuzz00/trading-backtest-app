"""
Lightweight OHLC Chart Widget using HTML/JavaScript

This widget uses lightweight-charts library for better performance
and a more professional UI for financial charting.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QComboBox, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QColor
import pandas as pd
import json
import os
import tempfile

class LightweightOHLCChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.temp_html_file = None
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Minimize margins
        layout.setSpacing(5)  # Minimize spacing
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Chart type selector
        control_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Candlestick", "Line", "Area"])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart_type)
        control_layout.addWidget(self.chart_type_combo)
        
        # Show trades toggle
        self.show_trades_btn = QPushButton("Hide Trades")
        self.show_trades_btn.setCheckable(True)
        self.show_trades_btn.setChecked(False)
        self.show_trades_btn.clicked.connect(self.toggle_trades)
        control_layout.addWidget(self.show_trades_btn)
        
        # Show/hide trades list
        self.show_trades_list_btn = QPushButton("Show Trades List")
        self.show_trades_list_btn.setCheckable(True)
        self.show_trades_list_btn.setChecked(False)
        self.show_trades_list_btn.clicked.connect(self.toggle_trades_list)
        control_layout.addWidget(self.show_trades_list_btn)
        
        # Status label (moved to control panel)
        self.status_label = QLabel("Run a backtest to see interactive OHLC chart")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        control_layout.addStretch()
        control_layout.addWidget(self.status_label)
        
        layout.addLayout(control_layout)
        
        # Splitter for chart and trades list
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)  # Prevent panels from collapsing
        
        # Left side: Chart container
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        
        # Create web view for chart
        self.web_view = QWebEngineView()
        # Enable developer tools for debugging
        try:
            from PyQt6.QtWebEngineCore import QWebEngineSettings
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        except Exception as e:
            print(f"Could not configure web engine settings: {e}")
        
        self.web_view.loadFinished.connect(self.on_load_finished)
        chart_layout.addWidget(self.web_view)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # Right side: Trades list table
        trades_container = QWidget()
        trades_layout = QVBoxLayout(trades_container)
        
        # Header for trades list
        trades_header = QLabel("📋 Trades List")
        trades_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        trades_layout.addWidget(trades_header)
        
        # Trades table
        self.trades_table = QTableWidget()
        self.trades_table.setAlternatingRowColors(True)
        self.trades_table.setSortingEnabled(True)
        headers = ["Date", "Action", "Type", "Price", "Quantity", "Value", "P&L", "P&L %"]
        self.trades_table.setColumnCount(len(headers))
        self.trades_table.setHorizontalHeaderLabels(headers)
        self.trades_table.horizontalHeader().setStretchLastSection(False)
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        trades_layout.addWidget(self.trades_table)
        trades_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add both containers to splitter
        self.splitter.addWidget(chart_container)
        self.splitter.addWidget(trades_container)
        
        # Set initial sizes (85% chart, 15% trades list)
        self.splitter.setSizes([850, 150])
        
        # Hide trades container initially
        trades_container.setVisible(False)
        
        # Add splitter to layout with stretch factor to fill all available space
        layout.addWidget(self.splitter, 1)  # Stretch factor of 1
        
        self.price_data = None
        self.trades = []
        self.show_trades_markers = True
        
        # Store reference to trades container for toggle
        self.trades_container = trades_container
    
    def on_load_finished(self, success):
        """Handle page load completion"""
        if success:
            num_candles = len(self.price_data) if self.price_data is not None else 0
            num_trades = len(self.trades) if self.trades else 0
            self.status_label.setText(f"Chart loaded: {num_candles} candles, {num_trades} trades")
            print(f"✓ Lightweight chart loaded successfully: {num_candles} candles, {num_trades} trades")
        else:
            self.status_label.setText("❌ Failed to load chart - Check if internet is available (CDN required)")
            print("✗ Chart load failed - The lightweight-charts library may not have loaded from CDN")
        
    def plot_ohlc_with_trades(self, price_data, trades):
        """
        Plot OHLC chart with trade markers using lightweight-charts
        
        Args:
            price_data: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
            trades: list of dicts with trade information
        """
        print(f"\n=== Lightweight Chart: plot_ohlc_with_trades called ===")
        print(f"Price data type: {type(price_data)}")
        print(f"Price data shape: {price_data.shape if price_data is not None else 'None'}")
        print(f"Trades count: {len(trades) if trades else 0}")
        
        if price_data is None or price_data.empty:
            self.status_label.setText("No price data available")
            print("✗ No price data to display")
            return
        
        print(f"Price data columns: {list(price_data.columns)}")
        
        # Use all price data from backtest (no limiting)
        self.price_data = price_data.copy()
        print(f"✓ Loading {len(self.price_data)} candles for chart")
        
        self.trades = trades
        
        # Ensure date column is datetime
        if 'date' in self.price_data.columns:
            self.price_data['date'] = pd.to_datetime(self.price_data['date'])
            print(f"✓ Date column converted to datetime")
        
        print(f"✓ Ready to render chart")
        
        # Update trades list
        self.update_trades_list()
        
        self.render_chart()
    
    def render_chart(self):
        """Render the chart with current data and settings - optimized with vectorization"""
        if self.price_data is None or self.price_data.empty:
            self.status_label.setText("No data to display")
            return
        
        print(f"Rendering chart with {len(self.price_data)} candles and {len(self.trades)} trades")
        
        # Vectorized data preparation for better performance
        try:
            # Ensure required columns exist
            required_cols = ['date', 'open', 'high', 'low', 'close']
            missing_cols = [col for col in required_cols if col not in self.price_data.columns]
            if missing_cols:
                self.status_label.setText(f"Missing required columns: {missing_cols}")
                print(f"✗ Missing columns: {missing_cols}")
                return
            
            # Convert all dates to timestamps at once (ensure timezone consistency)
            # Lightweight Charts expects Unix timestamps in SECONDS (not milliseconds)
            timestamps = self.price_data['date'].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
            
            # Debug: Print first and last timestamps
            if len(timestamps) > 0:
                print(f"First candle date: {self.price_data.iloc[0]['date']} -> timestamp: {timestamps[0]}")
                print(f"Last candle date: {self.price_data.iloc[-1]['date']} -> timestamp: {timestamps[-1]}")
            
            # Prepare chart data using list comprehension (faster than loop)
            chart_data = [
                {
                    'time': int(timestamps[i]),
                    'open': float(self.price_data.iloc[i]['open']),
                    'high': float(self.price_data.iloc[i]['high']),
                    'low': float(self.price_data.iloc[i]['low']),
                    'close': float(self.price_data.iloc[i]['close'])
                }
                for i in range(len(self.price_data))
            ]
            print(f"✓ Prepared {len(chart_data)} chart data points")
        except Exception as e:
            error_msg = f"Error processing chart data: {e}"
            print(f"✗ {error_msg}")
            self.status_label.setText(error_msg)
            return
        
        if not chart_data:
            self.status_label.setText("No valid chart data")
            return
        
        # Prepare volume data with vectorization
        volume_data = []
        if 'volume' in self.price_data.columns:
            try:
                # Determine colors vectorially
                is_bullish = (self.price_data['close'] >= self.price_data['open']).values
                colors = ['#26a69a' if bull else '#ef5350' for bull in is_bullish]
                
                volume_data = [
                    {
                        'time': int(timestamps[i]),  # Use same timestamps as chart_data
                        'value': float(self.price_data.iloc[i]['volume']) if self.price_data.iloc[i]['volume'] > 0 else 0.0,
                        'color': colors[i]
                    }
                    for i in range(len(self.price_data))
                ]
                print(f"✓ Prepared {len(volume_data)} volume data points")
            except Exception as e:
                print(f"⚠ Error processing volume data: {e}")
        
        # Prepare trade markers
        buy_long_markers = []
        sell_long_markers = []
        sell_short_markers = []
        buy_short_markers = []
        
        if self.show_trades_markers and self.trades:
            print(f"Processing {len(self.trades)} trade markers...")
            for trade in self.trades:
                try:
                    if 'date' not in trade:
                        continue
                        
                    trade_date = pd.to_datetime(trade['date'])
                    timestamp = int(pd.Timestamp(trade_date).timestamp())
                    price = float(trade.get('price', 0))
                    action = trade.get('action', '')
                    
                    # Debug: Print first trade timestamp
                    if len(buy_long_markers) == 0 and len(sell_long_markers) == 0 and len(sell_short_markers) == 0 and len(buy_short_markers) == 0:
                        print(f"First trade: {trade_date} -> timestamp: {timestamp}, action: {action}")
                    
                    # Long trades
                    if action in ['BUY', 'BUY_LONG']:
                        buy_long_markers.append({
                            'time': timestamp,
                            'position': 'belowBar',
                            'color': '#26a69a',
                            'shape': 'arrowUp',
                            'text': f"LONG @ ₹{price:.2f}"
                        })
                    elif action in ['SELL', 'SELL_LONG']:
                        sell_long_markers.append({
                            'time': timestamp,
                            'position': 'aboveBar',
                            'color': '#ef5350',
                            'shape': 'arrowDown',
                            'text': f"EXIT LONG @ ₹{price:.2f}"
                        })
                    # Short trades
                    elif action == 'SELL_SHORT':
                        sell_short_markers.append({
                            'time': timestamp,
                            'position': 'aboveBar',
                            'color': '#ff9800',
                            'shape': 'arrowDown',
                            'text': f"SHORT @ ₹{price:.2f}"
                        })
                    elif action == 'BUY_SHORT':
                        buy_short_markers.append({
                            'time': timestamp,
                            'position': 'belowBar',
                            'color': '#9c27b0',
                            'shape': 'arrowUp',
                            'text': f"COVER @ ₹{price:.2f}"
                        })
                except Exception as e:
                    print(f"Error processing trade marker: {e}")
                    continue
        
        all_markers = buy_long_markers + sell_long_markers + sell_short_markers + buy_short_markers
        all_markers.sort(key=lambda x: x['time'])
        print(f"✓ Prepared {len(all_markers)} trade markers (Long: {len(buy_long_markers)+len(sell_long_markers)}, Short: {len(sell_short_markers)+len(buy_short_markers)})")
        
        # Create HTML content
        html_content = self.generate_html(chart_data, volume_data, all_markers)
        
        # Save to temporary file and load
        if self.temp_html_file:
            try:
                os.unlink(self.temp_html_file)
            except:
                pass
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                self.temp_html_file = f.name
            
            print(f"✓ Created temporary HTML file: {self.temp_html_file}")
            self.web_view.setUrl(QUrl.fromLocalFile(self.temp_html_file))
            
            # Update status
            num_candles = len(chart_data)
            num_trades = len(self.trades)
            self.status_label.setText(f"Loading chart: {num_candles} candles | {num_trades} trades...")
        except Exception as e:
            error_msg = f"Error creating chart: {str(e)}"
            print(f"✗ {error_msg}")
            self.status_label.setText(error_msg)
    
    def generate_html(self, chart_data, volume_data, markers):
        """Generate HTML with lightweight-charts"""
        chart_data_json = json.dumps(chart_data)
        volume_data_json = json.dumps(volume_data)
        markers_json = json.dumps(markers)
        
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Chart</title>
    <script>
        // Error handler for CDN load failure
        window.addEventListener('error', function(e) {
            if (e.target.tagName === 'SCRIPT') {
                document.getElementById('chart-container').innerHTML = 
                    '<div style="padding:20px;color:red;font-family:Arial;text-align:center;">' +
                    '<h2>⚠ Chart Library Failed to Load</h2>' +
                    '<p>Could not load lightweight-charts from CDN.</p>' +
                    '<p>Please check your internet connection.</p>' +
                    '<p>The library loads from: unpkg.com</p>' +
                    '</div>';
            }
        }, true);
    </script>
    <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #ffffff;
        }
        #chart-container {
            width: 100%;
            height: 100vh;
            position: relative;
        }
        #main-chart {
            width: 100%;
            height: 85%;
        }
        #volume-chart {
            width: 100%;
            height: 15%;
        }
        .chart-info {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            z-index: 10;
        }
    </style>
</head>
<body>
    <div id="chart-container">
        <div class="chart-info" id="price-info">Loading chart...</div>
        <div id="main-chart"></div>
        <div id="volume-chart"></div>
    </div>
    
    <script>
        try {
            // Check if library loaded
            if (typeof LightweightCharts === 'undefined') {
                throw new Error('LightweightCharts library not loaded');
            }
            
            const mainChartContainer = document.getElementById('main-chart');
            const mainChart = LightweightCharts.createChart(mainChartContainer, {
                width: mainChartContainer.clientWidth,
                height: mainChartContainer.clientHeight,
                layout: {
                    background: { color: '#ffffff' },
                    textColor: '#333',
                },
                grid: {
                    vertLines: { color: '#f0f0f0' },
                    horzLines: { color: '#f0f0f0' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#cccccc',
                },
                timeScale: {
                    borderColor: '#cccccc',
                    timeVisible: true,
                    secondsVisible: false,
                },
            });
            
            const candlestickSeries = mainChart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderDownColor: '#ef5350',
                borderUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                wickUpColor: '#26a69a',
            });
            
            const chartData = CHART_DATA_PLACEHOLDER;
            candlestickSeries.setData(chartData);
            
            const markers = MARKERS_PLACEHOLDER;
            candlestickSeries.setMarkers(markers);
            
            const volumeChartContainer = document.getElementById('volume-chart');
            const volumeChart = LightweightCharts.createChart(volumeChartContainer, {
                width: volumeChartContainer.clientWidth,
                height: volumeChartContainer.clientHeight,
                layout: {
                    background: { color: '#ffffff' },
                    textColor: '#333',
                },
                grid: {
                    vertLines: { color: '#f0f0f0' },
                    horzLines: { color: '#f0f0f0' },
                },
                rightPriceScale: {
                    borderColor: '#cccccc',
                },
                timeScale: {
                    borderColor: '#cccccc',
                    visible: false,
                },
            });
            
            const volumeSeries = volumeChart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '',
            });
            
            const volumeData = VOLUME_DATA_PLACEHOLDER;
            volumeSeries.setData(volumeData);
            
            mainChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
                volumeChart.timeScale().setVisibleRange(timeRange);
            });
            
            window.addEventListener('resize', () => {
                mainChart.applyOptions({ 
                    width: mainChartContainer.clientWidth,
                    height: mainChartContainer.clientHeight 
                });
                volumeChart.applyOptions({ 
                    width: volumeChartContainer.clientWidth,
                    height: volumeChartContainer.clientHeight 
                });
            });
            
            const priceInfo = document.getElementById('price-info');
            mainChart.subscribeCrosshairMove((param) => {
                if (!param.time || !param.seriesData.get(candlestickSeries)) {
                    priceInfo.innerHTML = 'Hover over chart for details';
                    return;
                }
                
                const data = param.seriesData.get(candlestickSeries);
                const date = new Date(param.time * 1000).toLocaleDateString();
                
                priceInfo.innerHTML = `
                    <strong>${date}</strong><br>
                    O: $${data.open.toFixed(2)} | 
                    H: $${data.high.toFixed(2)} | 
                    L: $${data.low.toFixed(2)} | 
                    C: $${data.close.toFixed(2)}
                `;
            });
            
            mainChart.timeScale().fitContent();
            
            document.getElementById('price-info').innerHTML = '✓ Chart ready - Hover for details';
            console.log('Chart rendered successfully');
        } catch (error) {
            console.error('Chart error:', error);
            document.getElementById('chart-container').innerHTML = 
                '<div style="padding:20px;color:red;font-family:Arial;text-align:center;">' +
                '<h2>❌ Chart Error</h2>' +
                '<p>' + error.message + '</p>' +
                '<p>Check browser console for details.</p>' +
                '</div>';
        }
    </script>
</body>
</html>
""".replace('CHART_DATA_PLACEHOLDER', chart_data_json).replace('MARKERS_PLACEHOLDER', markers_json).replace('VOLUME_DATA_PLACEHOLDER', volume_data_json)
        
        return html
    
    def update_chart_type(self, chart_type):
        """Update chart type (will need to re-render)"""
        # For now, lightweight-charts best displays candlesticks
        # Could add line/area series if needed
        self.render_chart()
    
    def toggle_trades(self):
        """Toggle trade markers visibility"""
        self.show_trades_markers = not self.show_trades_btn.isChecked()
        if self.show_trades_btn.isChecked():
            self.show_trades_btn.setText("Show Trades")
        else:
            self.show_trades_btn.setText("Hide Trades")
        self.render_chart()
    
    def toggle_trades_list(self):
        """Toggle trades list panel visibility"""
        is_visible = self.trades_container.isVisible()
        self.trades_container.setVisible(not is_visible)
        
        if not is_visible:
            self.show_trades_list_btn.setText("Hide Trades List")
            # Show if hidden
            if not self.trades_container.isVisible():
                self.trades_container.setVisible(True)
        else:
            self.show_trades_list_btn.setText("Show Trades List")
    
    def update_trades_list(self):
        """Update the trades list table with current trades"""
        if not self.trades:
            self.trades_table.setRowCount(0)
            return
        
        print(f"Updating trades list with {len(self.trades)} trades")
        
        # Disable updates for faster rendering
        self.trades_table.setUpdatesEnabled(False)
        self.trades_table.setSortingEnabled(False)
        self.trades_table.blockSignals(True)
        
        self.trades_table.setRowCount(len(self.trades))
        
        # Pre-create color objects
        light_green = QColor(144, 238, 144)
        dark_green = QColor(0, 100, 0)
        light_red = QColor(255, 160, 160)
        dark_red = QColor(139, 0, 0)
        orange = QColor(200, 100, 0)
        purple = QColor(200, 150, 255)
        dark_purple = QColor(100, 0, 150)
        bright_green = QColor(0, 150, 0)
        very_light_green = QColor(200, 255, 200)
        bright_red = QColor(200, 0, 0)
        very_light_red = QColor(255, 220, 220)
        
        for i, trade in enumerate(self.trades):
            # Date
            date_str = str(trade.get('date', ''))[:10]  # Just the date part
            date_item = QTableWidgetItem(date_str)
            self.trades_table.setItem(i, 0, date_item)
            
            # Action
            action = trade.get('action', '')
            action_item = QTableWidgetItem(action)
            if action in ['BUY', 'BUY_LONG']:
                action_item.setBackground(light_green)
                action_item.setForeground(dark_green)
            elif action in ['SELL', 'SELL_LONG']:
                action_item.setBackground(light_red)
                action_item.setForeground(dark_red)
            elif action == 'SELL_SHORT':
                action_item.setBackground(QColor(255, 200, 150))
                action_item.setForeground(orange)
            elif action == 'BUY_SHORT':
                action_item.setBackground(purple)
                action_item.setForeground(dark_purple)
            self.trades_table.setItem(i, 1, action_item)
            
            # Trade Type
            trade_type = trade.get('trade_type', 'LONG')
            type_item = QTableWidgetItem(trade_type)
            if trade_type == 'LONG':
                type_item.setForeground(dark_green)
            else:
                type_item.setForeground(orange)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.trades_table.setItem(i, 2, type_item)
            
            # Price
            price = trade.get('price', 0)
            price_item = QTableWidgetItem(f"₹{price:,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 3, price_item)
            
            # Quantity
            quantity = trade.get('quantity', trade.get('shares', 0))
            qty_item = QTableWidgetItem(str(quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 4, qty_item)
            
            # Value
            value = trade.get('value', price * quantity)
            value_item = QTableWidgetItem(f"₹{value:,.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 5, value_item)
            
            # P&L (only for closing trades)
            pnl = trade.get('pnl', 0)
            if action in ['SELL', 'SELL_LONG', 'BUY_SHORT'] and pnl != 0:
                pnl_item = QTableWidgetItem(f"₹{pnl:,.2f}")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if pnl > 0:
                    pnl_item.setForeground(bright_green)
                    pnl_item.setBackground(very_light_green)
                elif pnl < 0:
                    pnl_item.setForeground(bright_red)
                    pnl_item.setBackground(very_light_red)
                self.trades_table.setItem(i, 6, pnl_item)
            else:
                pnl_item = QTableWidgetItem("-")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.trades_table.setItem(i, 6, pnl_item)
            
            # P&L %
            pnl_pct = trade.get('pnl_pct', 0)
            if action in ['SELL', 'SELL_LONG', 'BUY_SHORT'] and pnl_pct != 0:
                pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if pnl_pct > 0:
                    pnl_pct_item.setForeground(bright_green)
                    pnl_pct_item.setBackground(very_light_green)
                elif pnl_pct < 0:
                    pnl_pct_item.setForeground(bright_red)
                    pnl_pct_item.setBackground(very_light_red)
                self.trades_table.setItem(i, 7, pnl_pct_item)
            else:
                pnl_pct_item = QTableWidgetItem("-")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.trades_table.setItem(i, 7, pnl_pct_item)
        
        # Re-enable updates
        self.trades_table.blockSignals(False)
        self.trades_table.resizeColumnsToContents()
        self.trades_table.setSortingEnabled(True)
        self.trades_table.setUpdatesEnabled(True)
        
        print(f"✓ Trades list updated with {len(self.trades)} trades")
    
    def __del__(self):
        """Clean up temporary file"""
        if self.temp_html_file:
            try:
                os.unlink(self.temp_html_file)
            except:
                pass
