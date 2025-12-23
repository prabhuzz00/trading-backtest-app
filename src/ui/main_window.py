from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QTabWidget, QFileDialog,
    QDateEdit, QHBoxLayout, QMessageBox, QProgressBar, QApplication, QSplitter, QStatusBar
)
from PyQt6.QtCore import QThread, pyqtSignal, QDate, QTimer, Qt
from engine.backtest_engine import BacktestEngine
from ui.backtest_results import ResultsWidget
from ui.charts import ChartWidget
from ui.summary_widget import SummaryWidget
from ui.lightweight_ohlc_chart import LightweightOHLCChart
from ui.stock_sidebar import StockSidebar
from ui.top_toolbar import TopToolbar
from ui.styles import DARK_THEME
from utils.db_connection import get_available_stocks
import os
import yaml
from datetime import datetime, timedelta

class BacktestWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)  # progress percentage, status message

    def __init__(self, strategy_path, stock_symbol, start_date, end_date):
        super().__init__()
        self.strategy_path = strategy_path
        self.stock_symbol = stock_symbol
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            engine = BacktestEngine()
            results = engine.run_backtest(
                self.strategy_path,
                self.stock_symbol,
                self.start_date,
                self.end_date,
                progress_callback=self._emit_progress
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
    
    def _emit_progress(self, percentage, message):
        """Emit progress signal from backtest engine."""
        self.progress.emit(percentage, message)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Strategy Backtester")
        self.setGeometry(100, 100, 1600, 900)
        
        # Apply dark theme
        self.setStyleSheet(DARK_THEME)
        
        self.load_config()
        self.setup_ui()
        self.load_strategies()
        self.load_stocks_from_db()

    def load_config(self):
        cfg_path = os.path.join("config", "config.yaml")
        try:
            with open(cfg_path, "r") as f:
                self.config = yaml.safe_load(f)
        except Exception:
            self.config = {}

    def setup_ui(self):
        """Setup the UI with trading platform layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top toolbar
        self.toolbar = TopToolbar()
        self.toolbar.run_backtest_clicked.connect(self.run_backtest)
        main_layout.addWidget(self.toolbar)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #2A2E39; }")
        
        # Left sidebar - Stock list
        self.stock_sidebar = StockSidebar()
        self.stock_sidebar.stock_selected.connect(self.on_stock_selected)
        self.stock_sidebar.setMinimumWidth(200)
        self.stock_sidebar.setMaximumWidth(350)
        splitter.addWidget(self.stock_sidebar)
        
        # Right side - Chart and results area
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2A2E39;
                border: none;
                border-radius: 0;
                text-align: center;
                color: #D1D4DC;
                height: 3px;
            }
            QProgressBar::chunk {
                background-color: #2962FF;
                border-radius: 0;
            }
        """)
        right_layout.addWidget(self.progress_bar)
        
        # Results tabs (chart-focused)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #131722;
            }
            QTabBar::tab {
                background-color: #1E222D;
                color: #787B86;
                padding: 12px 24px;
                border: none;
                margin-right: 2px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #131722;
                color: #2962FF;
                border-bottom: 2px solid #2962FF;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2A2E39;
                color: #D1D4DC;
            }
        """)
        
        # Create tabs with chart as primary view
        self.ohlc_chart_widget = LightweightOHLCChart()
        self.chart_widget = ChartWidget()
        self.summary_widget = SummaryWidget()
        self.results_widget = ResultsWidget()
        
        self.tabs.addTab(self.ohlc_chart_widget, "📊 Chart")
        self.tabs.addTab(self.chart_widget, "📈 Equity Curve")
        self.tabs.addTab(self.summary_widget, "📋 Summary")
        self.tabs.addTab(self.results_widget, "💼 Trades")
        
        right_layout.addWidget(self.tabs)
        
        splitter.addWidget(right_widget)
        
        # Set initial splitter sizes (sidebar: 250px, main: rest)
        splitter.setSizes([250, 1350])
        
        main_layout.addWidget(splitter)
        
        # Status bar at bottom
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1E222D;
                color: #787B86;
                border-top: 1px solid #2A2E39;
                font-size: 12px;
            }
        """)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #787B86;")
        self.status_bar.addWidget(self.status_label)
        self.setStatusBar(self.status_bar)

    def load_strategies(self):
        """Load available strategies into toolbar"""
        strategies_dir = self.config.get("app", {}).get("strategies_dir", "strategies")
        if not os.path.isdir(strategies_dir):
            return
        files = [f for f in os.listdir(strategies_dir) if f.endswith(".py")]
        strategy_names = [os.path.splitext(f)[0] for f in files]
        self.toolbar.set_strategies(strategy_names)
    
    def load_stocks_from_db(self):
        """Load available stocks from MongoDB database into sidebar."""
        self.status_label.setText("Loading stocks from database...")
        try:
            stocks = get_available_stocks()
            if stocks:
                # Convert to list of dicts if needed (for future price/change display)
                stock_list = [{'symbol': s} if isinstance(s, str) else s for s in stocks]
                self.stock_sidebar.set_stocks(stock_list)
                self.status_label.setText(f"Loaded {len(stocks)} stocks")
            else:
                self.status_label.setText("No stocks found in database")
                QMessageBox.warning(self, "No Stocks", "No stock collections found in the database.")
        except Exception as e:
            self.status_label.setText(f"Error loading stocks: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"Failed to load stocks from database:\n{str(e)}")
    
    def on_stock_selected(self, symbol):
        """Handle stock selection from sidebar"""
        self.toolbar.set_symbol(symbol)
        self.status_label.setText(f"Selected: {symbol}")

    def add_strategy_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Strategy File", "", "Python Files (*.py)")
        if path:
            strategies_dir = self.config.get("app", {}).get("strategies_dir", "strategies")
            os.makedirs(strategies_dir, exist_ok=True)
            dest = os.path.join(strategies_dir, os.path.basename(path))
            try:
                with open(path, "r") as src, open(dest, "w") as dst:
                    dst.write(src.read())
                self.load_strategies()
            except Exception as e:
                print("Error copying strategy:", e)

    def run_backtest(self):
        """Run backtest with selected parameters"""
        # Get selected stock from sidebar
        selected_stock = self.stock_sidebar.get_selected_stock()
        if not selected_stock:
            QMessageBox.warning(self, "No Stock", "Please select a stock from the sidebar first.")
            return
        
        # Get selected strategy from toolbar
        strategy_name = self.toolbar.get_selected_strategy()
        if not strategy_name:
            QMessageBox.warning(self, "No Strategy", "Please select a strategy first.")
            return
        
        # Disable run button and update UI
        self.toolbar.set_running(True)
        self.status_label.setText("Running backtest...")
        
        strategy_path = os.path.join(
            self.config.get("app", {}).get("strategies_dir", "strategies"),
            f"{strategy_name}.py"
        )
        
        # Get date range from toolbar
        start_date, end_date = self.toolbar.get_date_range()
        
        self.worker = BacktestWorker(
            strategy_path=strategy_path,
            stock_symbol=selected_stock,
            start_date=start_date,
            end_date=end_date
        )
        self.worker.finished.connect(self.on_backtest_complete)
        self.worker.error.connect(self.on_backtest_error)
        self.worker.progress.connect(self.on_backtest_progress)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.worker.start()

    def on_backtest_progress(self, percentage, message):
        """Update progress bar during backtest."""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
        QApplication.processEvents()  # Keep UI responsive
    
    def on_backtest_complete(self, results):
        """Handle backtest completion"""
        self.progress_bar.setValue(100)
        self.status_label.setText("Processing results...")
        QApplication.processEvents()
        
        # Display summary first (fastest)
        self.summary_widget.display_summary(results)
        
        # Switch to chart tab to show results
        self.tabs.setCurrentIndex(0)
        QApplication.processEvents()
        
        # Lazy load other widgets using QTimer to avoid blocking UI
        QTimer.singleShot(100, lambda: self._load_results_delayed(results))
    
    def _load_results_delayed(self, results):
        """Load heavy UI components with delays to keep UI responsive."""
        # Load OHLC chart first (primary view)
        self.status_label.setText("Rendering chart...")
        QApplication.processEvents()
        
        price_data = results.get('price_data')
        trades = results.get('trades', [])
        if price_data is not None and not price_data.empty:
            self.ohlc_chart_widget.plot_ohlc_with_trades(price_data, trades)
        
        # Load equity chart with delay
        QTimer.singleShot(50, lambda: self._load_equity_chart(results))
    
    def _load_equity_chart(self, results):
        """Load equity chart."""
        self.status_label.setText("Rendering equity curve...")
        QApplication.processEvents()
        self.chart_widget.plot_equity_curve(results.get('equity_curve', []))
        
        # Load trade results last
        QTimer.singleShot(50, lambda: self._load_trade_results(results))
    
    def _load_trade_results(self, results):
        """Load trade results table."""
        self.status_label.setText("Loading trade results...")
        QApplication.processEvents()
        self.results_widget.display_results(results)
        
        # All done
        self._finalize_backtest_display(results)
    
    def _finalize_backtest_display(self, results):
        """Finalize the display after all widgets loaded."""
        self.toolbar.set_running(False)
        self.progress_bar.setVisible(False)
        
        # Display summary statistics
        trades_count = len(results.get('trades', []))
        metrics = results.get('metrics', {})
        total_return = metrics.get('total_return_pct', 0)
        color = "#26A69A" if total_return >= 0 else "#EF5350"
        self.status_label.setText(
            f"✓ Backtest complete! Trades: {trades_count} | "
            f"<span style='color: {color};'>Return: {total_return:.2f}%</span>"
        )

    def on_backtest_error(self, error_msg):
        """Handle backtest error"""
        print("Backtest error:", error_msg)
        self.status_label.setText(f"❌ Error: {error_msg}")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Backtest Error", f"An error occurred during backtest:\n{error_msg}")
        self.toolbar.set_running(False)