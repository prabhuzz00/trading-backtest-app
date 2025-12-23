"""
Top Toolbar Widget - Contains chart controls, strategy selection, and date range
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QDateEdit, QToolButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QIcon


class Separator(QFrame):
    """Vertical separator line"""
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyleSheet("color: #2A2E39;")
        self.setFixedWidth(1)


class TopToolbar(QWidget):
    """Top toolbar with trading controls"""
    run_backtest_clicked = pyqtSignal()
    strategy_changed = pyqtSignal(str)
    date_range_changed = pyqtSignal(str, str)  # start_date, end_date
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #1E222D; border-bottom: 1px solid #2A2E39;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Symbol display (will be updated when stock is selected)
        self.symbol_label = QLabel("Select Symbol")
        self.symbol_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.symbol_label)
        
        # Price display
        self.price_label = QLabel("")
        self.price_label.setStyleSheet("font-size: 14px; color: #D1D4DC; margin-left: 12px;")
        layout.addWidget(self.price_label)
        
        layout.addStretch()
        
        # Strategy selector
        layout.addWidget(QLabel("Strategy:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.setMinimumWidth(180)
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)
        layout.addWidget(self.strategy_combo)
        
        layout.addWidget(Separator())
        
        # Date range
        layout.addWidget(QLabel("Start:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setFixedWidth(120)
        self.start_date.dateChanged.connect(self.on_date_changed)
        layout.addWidget(self.start_date)
        
        layout.addWidget(QLabel("End:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setFixedWidth(120)
        self.end_date.dateChanged.connect(self.on_date_changed)
        layout.addWidget(self.end_date)
        
        layout.addWidget(Separator())
        
        # Run backtest button
        self.run_btn = QPushButton("Run Backtest")
        self.run_btn.setFixedWidth(120)
        self.run_btn.clicked.connect(self.on_run_clicked)
        layout.addWidget(self.run_btn)
        
        # Indicators button (placeholder for future features)
        self.indicators_btn = QPushButton("Indicators")
        self.indicators_btn.setObjectName("secondaryButton")
        self.indicators_btn.setFixedWidth(100)
        self.indicators_btn.setEnabled(False)
        layout.addWidget(self.indicators_btn)
    
    def set_strategies(self, strategies):
        """Set available strategies"""
        self.strategy_combo.clear()
        self.strategy_combo.addItems(strategies)
    
    def get_selected_strategy(self):
        """Get currently selected strategy"""
        return self.strategy_combo.currentText()
    
    def set_symbol(self, symbol, price=None, change_pct=None):
        """Update symbol display"""
        self.symbol_label.setText(symbol)
        
        if price is not None:
            price_text = f"₹{price:,.2f}"
            if change_pct is not None:
                color = "#26A69A" if change_pct >= 0 else "#EF5350"
                sign = "+" if change_pct >= 0 else ""
                price_text += f"  <span style='color: {color};'>{sign}{change_pct:.2f}%</span>"
            self.price_label.setText(price_text)
        else:
            self.price_label.setText("")
    
    def get_date_range(self):
        """Get selected date range"""
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        return start, end
    
    def set_running(self, running=True):
        """Set running state"""
        if running:
            self.run_btn.setEnabled(False)
            self.run_btn.setText("Running...")
        else:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("Run Backtest")
    
    def on_strategy_changed(self, strategy):
        """Handle strategy change"""
        if strategy:
            self.strategy_changed.emit(strategy)
    
    def on_date_changed(self):
        """Handle date range change"""
        start, end = self.get_date_range()
        self.date_range_changed.emit(start, end)
    
    def on_run_clicked(self):
        """Handle run button click"""
        self.run_backtest_clicked.emit()
