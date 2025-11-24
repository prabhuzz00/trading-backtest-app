from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QTabWidget, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal
from engine.backtest_engine import BacktestEngine
from ui.backtest_results import ResultsWidget
from ui.charts import ChartWidget
import os
import yaml

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
        self.setup_ui()
        self.load_config()
        self.load_strategies()

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

        self.strategy_combo = QComboBox()
        layout.addWidget(QLabel("Select Strategy:"))
        layout.addWidget(self.strategy_combo)

        self.load_strategy_btn = QPushButton("Add Strategy (file)")
        self.load_strategy_btn.clicked.connect(self.add_strategy_file)
        layout.addWidget(self.load_strategy_btn)

        self.stock_combo = QComboBox()
        self.stock_combo.addItems(["AAPL", "MSFT", "TSLA"])
        layout.addWidget(QLabel("Select Stock:"))
        layout.addWidget(self.stock_combo)

        self.run_btn = QPushButton("Run Backtest")
        self.run_btn.clicked.connect(self.run_backtest)
        layout.addWidget(self.run_btn)

        self.tabs = QTabWidget()
        self.results_widget = ResultsWidget()
        self.chart_widget = ChartWidget()
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
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")
        strategy_name = self.strategy_combo.currentText()
        strategy_path = os.path.join(self.config.get("app", {}).get("strategies_dir", "strategies"), f"{strategy_name}.py")
        self.worker = BacktestWorker(
            strategy_path=strategy_path,
            stock_symbol=self.stock_combo.currentText(),
            start_date="2023-01-01",
            end_date="2024-01-01"
        )
        self.worker.finished.connect(self.on_backtest_complete)
        self.worker.error.connect(self.on_backtest_error)
        self.worker.start()

    def on_backtest_complete(self, results):
        self.results_widget.display_results(results)
        self.chart_widget.plot_equity_curve(results.get('equity_curve', []))
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Backtest")

    def on_backtest_error(self, error_msg):
        print("Backtest error:", error_msg)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Backtest")