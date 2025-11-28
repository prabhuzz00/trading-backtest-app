from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QTabWidget, QFileDialog,
    QDateEdit, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QDate
from engine.backtest_engine import BacktestEngine
from ui.backtest_results import ResultsWidget
from ui.charts import ChartWidget
from ui.summary_widget import SummaryWidget
from utils.db_connection import get_available_stocks
import os
import yaml
from datetime import datetime, timedelta

class BacktestWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

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
                self.end_date
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Strategy Backtester")
        self.setGeometry(100, 100, 1200, 800)
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Strategy selection
        self.strategy_combo = QComboBox()
        layout.addWidget(QLabel("Select Strategy:"))
        layout.addWidget(self.strategy_combo)

        self.load_strategy_btn = QPushButton("Add Strategy (file)")
        self.load_strategy_btn.clicked.connect(self.add_strategy_file)
        layout.addWidget(self.load_strategy_btn)

        # Stock selection
        self.stock_combo = QComboBox()
        self.stock_combo.setEditable(True)  # Allow searching
        layout.addWidget(QLabel("Select Stock:"))
        layout.addWidget(self.stock_combo)
        
        # Refresh stocks button
        self.refresh_stocks_btn = QPushButton("Refresh Stock List")
        self.refresh_stocks_btn.clicked.connect(self.load_stocks_from_db)
        layout.addWidget(self.refresh_stocks_btn)

        # Date range selection
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start Date:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("End Date:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.end_date)
        layout.addLayout(date_layout)

        # Run button
        self.run_btn = QPushButton("Run Backtest")
        self.run_btn.clicked.connect(self.run_backtest)
        layout.addWidget(self.run_btn)

        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Results tabs
        self.tabs = QTabWidget()
        self.summary_widget = SummaryWidget()
        self.results_widget = ResultsWidget()
        self.chart_widget = ChartWidget()
        self.tabs.addTab(self.summary_widget, "Summary")
        self.tabs.addTab(self.results_widget, "Trade Results")
        self.tabs.addTab(self.chart_widget, "Charts")
        layout.addWidget(self.tabs)

    def load_strategies(self):
        strategies_dir = self.config.get("app", {}).get("strategies_dir", "strategies")
        if not os.path.isdir(strategies_dir):
            return
        files = [f for f in os.listdir(strategies_dir) if f.endswith(".py")]
        self.strategy_combo.clear()
        self.strategy_combo.addItems([os.path.splitext(f)[0] for f in files])
    
    def load_stocks_from_db(self):
        """Load available stocks from MongoDB database."""
        self.status_label.setText("Loading stocks from database...")
        self.refresh_stocks_btn.setEnabled(False)
        try:
            stocks = get_available_stocks()
            self.stock_combo.clear()
            if stocks:
                self.stock_combo.addItems(stocks)
                self.status_label.setText(f"Loaded {len(stocks)} stocks")
            else:
                self.status_label.setText("No stocks found in database")
                QMessageBox.warning(self, "No Stocks", "No stock collections found in the database.")
        except Exception as e:
            self.status_label.setText(f"Error loading stocks: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"Failed to load stocks from database:\n{str(e)}")
        finally:
            self.refresh_stocks_btn.setEnabled(True)

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
        # Validate inputs
        if not self.strategy_combo.currentText():
            QMessageBox.warning(self, "No Strategy", "Please select a strategy first.")
            return
        if not self.stock_combo.currentText():
            QMessageBox.warning(self, "No Stock", "Please select a stock first.")
            return
        
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")
        self.status_label.setText("Running backtest...")
        
        strategy_name = self.strategy_combo.currentText()
        strategy_path = os.path.join(self.config.get("app", {}).get("strategies_dir", "strategies"), f"{strategy_name}.py")
        
        # Get date range from UI
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        self.worker = BacktestWorker(
            strategy_path=strategy_path,
            stock_symbol=self.stock_combo.currentText(),
            start_date=start_date,
            end_date=end_date
        )
        self.worker.finished.connect(self.on_backtest_complete)
        self.worker.error.connect(self.on_backtest_error)
        self.worker.start()

    def on_backtest_complete(self, results):
        self.summary_widget.display_summary(results)
        self.results_widget.display_results(results)
        self.chart_widget.plot_equity_curve(results.get('equity_curve', []))
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Backtest")
        
        # Display summary statistics
        trades_count = len(results.get('trades', []))
        metrics = results.get('metrics', {})
        total_return = metrics.get('total_return_pct', 0)
        self.status_label.setText(f"Backtest complete! Trades: {trades_count} | Return: {total_return:.2f}%")
        
        # Switch to summary tab to show results
        self.tabs.setCurrentIndex(0)

    def on_backtest_error(self, error_msg):
        print("Backtest error:", error_msg)
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Backtest Error", f"An error occurred during backtest:\n{error_msg}")
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Backtest")