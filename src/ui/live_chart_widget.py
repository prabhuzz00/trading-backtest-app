"""
Live Chart Widget - Displays OHLCV data for selected instrument from MongoDB
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QDateEdit, QMessageBox, QProgressBar, QApplication
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QColor
import pandas as pd
import json
import os
import tempfile
from datetime import datetime, timedelta
from utils.db_connection import get_stock_data


class DataFetchWorker(QThread):
    """Background worker for fetching data from MongoDB"""
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, symbol, start_date, end_date):
        super().__init__()
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
    
    def run(self):
        try:
            self.progress.emit(f"Fetching {self.symbol} data...")
            df = get_stock_data(self.symbol, self.start_date, self.end_date, use_cache=False)
            
            if df.empty:
                self.error.emit(f"No data found for {self.symbol}")
            else:
                self.progress.emit(f"Loaded {len(df)} candles")
                self.finished.emit(df)
        except Exception as e:
            self.error.emit(f"Error fetching data: {str(e)}")


class LiveChartWidget(QWidget):
    """Widget for displaying live OHLCV data from MongoDB"""
    
    def __init__(self):
        super().__init__()
        self.current_symbol = None
        self.current_data = None
        self.temp_html_file = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Control panel
        control_panel = QWidget()
        control_panel.setFixedHeight(50)
        control_panel.setStyleSheet("""
            QWidget {
                background-color: #1E222D;
                border-bottom: 1px solid #2A2E39;
            }
        """)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(12, 6, 12, 6)
        control_layout.setSpacing(8)
        
        # Symbol label
        self.symbol_label = QLabel("No symbol selected")
        self.symbol_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #D1D4DC;")
        control_layout.addWidget(self.symbol_label)
        
        control_layout.addStretch()
        
        # Date presets (compact buttons)
        presets_label = QLabel("Period:")
        presets_label.setStyleSheet("color: #787B86; font-size: 11px;")
        control_layout.addWidget(presets_label)
        
        self.preset_buttons = []
        presets = [("1W", 7), ("1M", 30), ("3M", 90), ("6M", 180), ("1Y", 365), ("All", None)]
        for label, days in presets:
            btn = QPushButton(label)
            btn.setFixedSize(35, 28)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2A2E39;
                    color: #D1D4DC;
                    border: 1px solid #363A45;
                    border-radius: 3px;
                    font-size: 11px;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: #363A45;
                    border-color: #2962FF;
                }
                QPushButton:pressed {
                    background-color: #2962FF;
                }
            """)
            btn.clicked.connect(lambda checked, d=days: self.set_date_preset(d))
            control_layout.addWidget(btn)
            self.preset_buttons.append(btn)
        
        # Separator
        sep = QLabel("|")
        sep.setStyleSheet("color: #2A2E39; font-size: 16px;")
        control_layout.addWidget(sep)
        
        # Timeframe selector
        timeframe_label = QLabel("TF:")
        timeframe_label.setStyleSheet("color: #787B86; font-size: 11px;")
        control_layout.addWidget(timeframe_label)
        
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1min", "3min", "5min", "15min", "30min", "1D", "1W", "1M"])
        self.timeframe_combo.setCurrentText("1min")
        self.timeframe_combo.setFixedWidth(65)
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        control_layout.addWidget(self.timeframe_combo)
        
        # Chart type selector (compact)
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Candlestick", "Line", "Area"])
        self.chart_type_combo.setFixedWidth(100)
        self.chart_type_combo.currentTextChanged.connect(self.update_chart_type)
        control_layout.addWidget(self.chart_type_combo)
        
        # Date range selector (hidden by default, accessible via button)
        self.custom_date_btn = QPushButton("📅")
        self.custom_date_btn.setFixedSize(28, 28)
        self.custom_date_btn.setToolTip("Custom date range")
        self.custom_date_btn.setCheckable(True)
        self.custom_date_btn.setStyleSheet("""
            QPushButton {
                background-color: #2A2E39;
                color: #D1D4DC;
                border: 1px solid #363A45;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #363A45;
                border-color: #2962FF;
            }
            QPushButton:checked {
                background-color: #2962FF;
                border-color: #2962FF;
            }
        """)
        self.custom_date_btn.clicked.connect(self.toggle_custom_dates)
        control_layout.addWidget(self.custom_date_btn)
        
        # Custom date container (initially hidden)
        self.custom_date_container = QWidget()
        custom_date_layout = QHBoxLayout(self.custom_date_container)
        custom_date_layout.setContentsMargins(0, 0, 0, 0)
        custom_date_layout.setSpacing(6)
        
        from_label = QLabel("From:")
        from_label.setStyleSheet("color: #787B86; font-size: 11px;")
        custom_date_layout.addWidget(from_label)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.setDisplayFormat("dd-MMM-yy")
        self.start_date.setFixedWidth(90)
        self.start_date.setStyleSheet("""
            QDateEdit {
                background-color: #2A2E39;
                color: #D1D4DC;
                border: 1px solid #363A45;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 11px;
            }
        """)
        custom_date_layout.addWidget(self.start_date)
        
        to_label = QLabel("To:")
        to_label.setStyleSheet("color: #787B86; font-size: 11px;")
        custom_date_layout.addWidget(to_label)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("dd-MMM-yy")
        self.end_date.setFixedWidth(90)
        self.end_date.setStyleSheet("""
            QDateEdit {
                background-color: #2A2E39;
                color: #D1D4DC;
                border: 1px solid #363A45;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 11px;
            }
        """)
        custom_date_layout.addWidget(self.end_date)
        
        self.custom_date_container.setVisible(False)
        control_layout.addWidget(self.custom_date_container)
        
        # Refresh button
        self.refresh_btn = QPushButton("📊 Load Chart")
        self.refresh_btn.setObjectName("secondaryButton")
        self.refresh_btn.clicked.connect(self.load_chart_data)
        self.refresh_btn.setEnabled(False)
        control_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(control_panel)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2A2E39;
                border: none;
                text-align: center;
                color: #D1D4DC;
                height: 3px;
            }
            QProgressBar::chunk {
                background-color: #2962FF;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Web view for chart
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background-color: #131722;")
        
        # Enable settings
        try:
            from PyQt6.QtWebEngineCore import QWebEngineSettings
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        except Exception as e:
            print(f"Could not configure web engine settings: {e}")
        
        self.web_view.loadFinished.connect(self.on_load_finished)
        layout.addWidget(self.web_view)
        
        # Status label
        self.status_label = QLabel("Select a symbol from the sidebar to view chart")
        self.status_label.setFixedHeight(28)
        self.status_label.setStyleSheet("""
            color: #787B86; 
            padding: 4px 12px;
            background-color: #1E222D;
            border-top: 1px solid #2A2E39;
            font-size: 11px;
        """)
        layout.addWidget(self.status_label)
        
        # Load empty chart
        self.load_empty_chart()
    
    def set_date_preset(self, days):
        """Set date range based on preset"""
        self.end_date.setDate(QDate.currentDate())
        if days is None:
            # "All" - set to a very old date (5 years ago)
            self.start_date.setDate(QDate.currentDate().addYears(-5))
        else:
            self.start_date.setDate(QDate.currentDate().addDays(-days))
        
        # Auto-load if symbol is selected
        if self.current_symbol:
            self.load_chart_data()
    
    def toggle_custom_dates(self, checked):
        """Toggle visibility of custom date selectors"""
        self.custom_date_container.setVisible(checked)
    
    def set_symbol(self, symbol):
        """Set the current symbol and enable loading"""
        self.current_symbol = symbol
        self.symbol_label.setText(symbol)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Select a period or click 'Load Chart' for {symbol}")
    
    def load_chart_data(self):
        """Load data from MongoDB and display chart"""
        if not self.current_symbol:
            QMessageBox.warning(self, "No Symbol", "Please select a symbol from the sidebar first.")
            return
        
        # Get date range
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        # Disable button and show progress
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Fetching data from MongoDB...")
        
        # Start background worker
        self.worker = DataFetchWorker(self.current_symbol, start_date, end_date)
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.error.connect(self.on_data_error)
        self.worker.progress.connect(self.on_progress)
        self.worker.start()
    
    def on_progress(self, message):
        """Update progress message"""
        self.status_label.setText(message)
        QApplication.processEvents()
    
    def on_data_loaded(self, df):
        """Handle loaded data"""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
        if df.empty:
            self.status_label.setText("No data available for selected date range")
            return
        
        # Store raw data
        self.current_data = df
        
        # Apply timeframe aggregation
        aggregated_df = self.aggregate_timeframe(df, self.timeframe_combo.currentText())
        self.plot_chart(aggregated_df)
        
        # Update status
        start_date = aggregated_df['date'].min().strftime('%Y-%m-%d')
        end_date = aggregated_df['date'].max().strftime('%Y-%m-%d')
        timeframe = self.timeframe_combo.currentText()
        self.status_label.setText(
            f"✓ Loaded {len(aggregated_df)} candles ({timeframe}) | "
            f"Period: {start_date} to {end_date} | "
            f"Latest: ₹{aggregated_df['close'].iloc[-1]:,.2f}"
        )
    
    def aggregate_timeframe(self, df, timeframe):
        """Aggregate data to specified timeframe"""
        if df.empty:
            return df
        
        # If already 1min and requesting 1min, return as is
        if timeframe == "1min":
            return df
        
        # Copy and set date as index for resampling
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        df_copy.set_index('date', inplace=True)
        
        # Map timeframe to pandas frequency
        freq_map = {
            "3min": "3T",
            "5min": "5T",
            "15min": "15T",
            "30min": "30T",
            "1D": "1D",
            "1W": "1W",
            "1M": "1M"
        }
        
        freq = freq_map.get(timeframe, "1T")
        
        # Resample OHLCV data
        aggregated = df_copy.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Reset index to get date column back
        aggregated.reset_index(inplace=True)
        
        return aggregated
    
    def on_timeframe_changed(self, timeframe):
        """Handle timeframe change"""
        if self.current_data is not None and not self.current_data.empty:
            # Re-aggregate and plot with new timeframe
            aggregated_df = self.aggregate_timeframe(self.current_data, timeframe)
            self.plot_chart(aggregated_df)
            
            # Update status
            start_date = aggregated_df['date'].min().strftime('%Y-%m-%d')
            end_date = aggregated_df['date'].max().strftime('%Y-%m-%d')
            self.status_label.setText(
                f"✓ {len(aggregated_df)} candles ({timeframe}) | "
                f"Period: {start_date} to {end_date} | "
                f"Latest: ₹{aggregated_df['close'].iloc[-1]:,.2f}"
            )
    
    def on_data_error(self, error_msg):
        """Handle data loading error"""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"❌ {error_msg}")
        QMessageBox.critical(self, "Data Error", error_msg)
    
    def plot_chart(self, df):
        """Plot OHLCV data in lightweight chart"""
        if df.empty:
            return
        
        # Prepare data for JavaScript
        chart_data = []
        for _, row in df.iterrows():
            chart_data.append({
                'time': int(row['date'].timestamp()),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'value': float(row['close']),  # For line/area charts
            })
        
        # Prepare volume data
        volume_data = []
        for _, row in df.iterrows():
            volume_data.append({
                'time': int(row['date'].timestamp()),
                'value': float(row['volume']),
                'color': '#26A69A' if row['close'] >= row['open'] else '#EF5350'
            })
        
        chart_type = self.chart_type_combo.currentText().lower().replace(" ", "")
        
        # Generate HTML
        html_content = self.generate_chart_html(chart_data, volume_data, chart_type)
        
        # Save to temp file and load
        if self.temp_html_file:
            try:
                os.remove(self.temp_html_file)
            except:
                pass
        
        self.temp_html_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8')
        self.temp_html_file.write(html_content)
        self.temp_html_file.close()
        
        self.web_view.setUrl(QUrl.fromLocalFile(self.temp_html_file.name))
    
    def load_empty_chart(self):
        """Load empty chart on initialization"""
        html_content = self.generate_chart_html([], [], 'candlestick')
        
        self.temp_html_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8')
        self.temp_html_file.write(html_content)
        self.temp_html_file.close()
        
        self.web_view.setUrl(QUrl.fromLocalFile(self.temp_html_file.name))
    
    def update_chart_type(self, chart_type):
        """Update chart type"""
        if self.current_data is not None and not self.current_data.empty:
            self.plot_chart(self.current_data)
    
    def generate_chart_html(self, chart_data, volume_data, chart_type='candlestick'):
        """Generate HTML with lightweight-charts"""
        
        chart_data_json = json.dumps(chart_data)
        volume_data_json = json.dumps(volume_data)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Chart</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #131722;
            overflow: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        #chart {{
            width: 100%;
            height: 75%;
            flex-grow: 1;
        }}
        #volume {{
            width: 100%;
            height: 25%;
            flex-shrink: 0;
        }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <div id="volume"></div>
    
    <script>
        try {{
            // Check if library loaded
            if (typeof LightweightCharts === 'undefined') {{
                throw new Error('LightweightCharts library not loaded');
            }}
            
            // Chart data
            const chartData = {chart_data_json};
            const volumeData = {volume_data_json};
            
            // Main chart
            const chartContainer = document.getElementById('chart');
            const chart = LightweightCharts.createChart(chartContainer, {{
                width: chartContainer.clientWidth,
                height: chartContainer.clientHeight,
                layout: {{
                    background: {{ color: '#131722' }},
                    textColor: '#D1D4DC',
                }},
                grid: {{
                    vertLines: {{ color: '#2A2E39' }},
                    horzLines: {{ color: '#2A2E39' }},
                }},
                crosshair: {{
                    mode: LightweightCharts.CrosshairMode.Normal,
                }},
                rightPriceScale: {{
                    borderColor: '#2A2E39',
                }},
                timeScale: {{
                    borderColor: '#2A2E39',
                    timeVisible: true,
                    secondsVisible: false,
                }},
            }});
            
            // Add main series based on chart type
            let mainSeries;
            const chartType = '{chart_type}';
            
            if (chartType === 'candlestick') {{
                mainSeries = chart.addCandlestickSeries({{
                    upColor: '#26A69A',
                    downColor: '#EF5350',
                    borderUpColor: '#26A69A',
                    borderDownColor: '#EF5350',
                    wickUpColor: '#26A69A',
                    wickDownColor: '#EF5350',
                }});
            }} else if (chartType === 'line') {{
                mainSeries = chart.addLineSeries({{
                    color: '#2962FF',
                    lineWidth: 2,
                }});
            }} else if (chartType === 'area') {{
                mainSeries = chart.addAreaSeries({{
                    topColor: 'rgba(41, 98, 255, 0.4)',
                    bottomColor: 'rgba(41, 98, 255, 0.0)',
                    lineColor: '#2962FF',
                    lineWidth: 2,
                }});
            }}
            
            mainSeries.setData(chartData);
            
            // Volume chart
            const volumeContainer = document.getElementById('volume');
            const volumeChart = LightweightCharts.createChart(volumeContainer, {{
                width: volumeContainer.clientWidth,
                height: volumeContainer.clientHeight,
                layout: {{
                    background: {{ color: '#131722' }},
                    textColor: '#D1D4DC',
                }},
                grid: {{
                    vertLines: {{ color: '#2A2E39' }},
                    horzLines: {{ color: '#2A2E39' }},
                }},
                rightPriceScale: {{
                    borderColor: '#2A2E39',
                }},
                timeScale: {{
                    borderColor: '#2A2E39',
                    timeVisible: true,
                    secondsVisible: false,
                }},
            }});
            
            const volumeSeries = volumeChart.addHistogramSeries({{
                priceFormat: {{
                    type: 'volume',
                }},
                priceScaleId: '',
            }});
            
            volumeSeries.setData(volumeData);
            
            // Sync time scales
            chart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {{
                volumeChart.timeScale().setVisibleRange(timeRange);
            }});
            
            volumeChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {{
                chart.timeScale().setVisibleRange(timeRange);
            }});
            
            // Auto-resize
            window.addEventListener('resize', () => {{
                chart.applyOptions({{ width: chartContainer.clientWidth }});
                volumeChart.applyOptions({{ width: volumeContainer.clientWidth }});
            }});
            
            // Fit content
            if (chartData.length > 0) {{
                chart.timeScale().fitContent();
                volumeChart.timeScale().fitContent();
            }}
        }} catch (error) {{
            console.error('Chart error:', error);
            document.body.innerHTML = '<div style="color: #EF5350; padding: 20px;">Error loading chart: ' + error.message + '</div>';
        }}
    </script>
</body>
</html>
        """
        
        return html
    
    def on_load_finished(self, success):
        """Handle chart load completion"""
        if not success:
            print("Chart failed to load")
    
    def __del__(self):
        """Cleanup temp file"""
        if self.temp_html_file:
            try:
                os.remove(self.temp_html_file)
            except:
                pass
