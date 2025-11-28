from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QScrollArea
from PyQt6.QtCore import Qt

class SummaryWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for responsive content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Backtest Summary")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; color: #FFFFFF;")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Create grid layout for metrics
        self.grid = QGridLayout()
        self.grid.setSpacing(15)
        self.grid.setColumnStretch(0, 1)  # Label column
        self.grid.setColumnStretch(1, 1)  # Value column
        layout.addLayout(self.grid)
        
        # Initialize metric labels
        self.metric_labels = {}
        
        layout.addStretch()
        
        # Set the content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def create_metric_row(self, label_text, value_text, row):
        """Create a row with label and value."""
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF; padding: 5px;")
        label.setWordWrap(True)
        label.setMinimumWidth(150)
        
        value = QLabel(value_text)
        value.setStyleSheet("font-size: 12px; color: #ADD8E6; padding: 5px;")
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value.setWordWrap(True)
        value.setMinimumWidth(100)
        
        self.grid.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.grid.addWidget(value, row, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        return value
    
    def display_summary(self, results):
        """Display summary metrics from backtest results."""
        # Clear existing widgets
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
        
        self.metric_labels.clear()
        
        metrics = results.get('metrics', {})
        
        if not metrics:
            no_data = QLabel("Run a backtest to see summary metrics")
            no_data.setStyleSheet("font-style: italic; color: gray; padding: 20px;")
            no_data.setWordWrap(True)
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(no_data, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
            return
        
        row = 0
        
        # Performance Metrics
        section_label = QLabel("📊 Performance Metrics")
        section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #87CEEB; padding-top: 10px; padding-bottom: 5px;")
        section_label.setWordWrap(True)
        self.grid.addWidget(section_label, row, 0, 1, 2)
        row += 1
        
        self.metric_labels['total_return'] = self.create_metric_row(
            "Total Return:", 
            f"{metrics.get('total_return_pct', 0):.2f}%", 
            row
        )
        row += 1
        
        self.metric_labels['total_pnl'] = self.create_metric_row(
            "Total P&L:", 
            f"₹{metrics.get('total_pnl', 0):,.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['initial_capital'] = self.create_metric_row(
            "Initial Capital:", 
            f"₹{metrics.get('initial_capital', 0):,.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['final_capital'] = self.create_metric_row(
            "Final Capital:", 
            f"₹{metrics.get('final_capital', 0):,.2f}", 
            row
        )
        row += 1
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ccc;")
        self.grid.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Trade Statistics
        section_label = QLabel("📈 Trade Statistics")
        section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #87CEEB; padding-top: 10px; padding-bottom: 5px;")
        section_label.setWordWrap(True)
        self.grid.addWidget(section_label, row, 0, 1, 2)
        row += 1
        
        self.metric_labels['total_trades'] = self.create_metric_row(
            "Total Trades:", 
            str(metrics.get('total_trades', 0)), 
            row
        )
        row += 1
        
        self.metric_labels['winning_trades'] = self.create_metric_row(
            "Winning Trades:", 
            str(metrics.get('winning_trades', 0)), 
            row
        )
        row += 1
        
        self.metric_labels['losing_trades'] = self.create_metric_row(
            "Losing Trades:", 
            str(metrics.get('losing_trades', 0)), 
            row
        )
        row += 1
        
        self.metric_labels['win_rate'] = self.create_metric_row(
            "Win Rate:", 
            f"{metrics.get('win_rate', 0):.2f}%", 
            row
        )
        row += 1
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ccc;")
        self.grid.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Profit/Loss Analysis
        section_label = QLabel("💰 Profit/Loss Analysis")
        section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #87CEEB; padding-top: 10px; padding-bottom: 5px;")
        section_label.setWordWrap(True)
        self.grid.addWidget(section_label, row, 0, 1, 2)
        row += 1
        
        self.metric_labels['gross_profit'] = self.create_metric_row(
            "Gross Profit:", 
            f"₹{metrics.get('gross_profit', 0):,.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['gross_loss'] = self.create_metric_row(
            "Gross Loss:", 
            f"₹{metrics.get('gross_loss', 0):,.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['profit_factor'] = self.create_metric_row(
            "Profit Factor:", 
            f"{metrics.get('profit_factor', 0):.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['avg_win'] = self.create_metric_row(
            "Average Win:", 
            f"₹{metrics.get('avg_win', 0):,.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['avg_loss'] = self.create_metric_row(
            "Average Loss:", 
            f"₹{metrics.get('avg_loss', 0):,.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['largest_win'] = self.create_metric_row(
            "Largest Win:", 
            f"₹{metrics.get('largest_win', 0):,.2f}", 
            row
        )
        row += 1
        
        self.metric_labels['largest_loss'] = self.create_metric_row(
            "Largest Loss:", 
            f"₹{metrics.get('largest_loss', 0):,.2f}", 
            row
        )
        row += 1
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ccc;")
        self.grid.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Risk Metrics
        section_label = QLabel("⚠️ Risk Metrics")
        section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #87CEEB; padding-top: 10px; padding-bottom: 5px;")
        section_label.setWordWrap(True)
        self.grid.addWidget(section_label, row, 0, 1, 2)
        row += 1
        
        self.metric_labels['max_drawdown'] = self.create_metric_row(
            "Max Drawdown:", 
            f"{metrics.get('max_drawdown_pct', 0):.2f}%", 
            row
        )
        row += 1
        
        self.metric_labels['max_drawdown_value'] = self.create_metric_row(
            "Max Drawdown Value:", 
            f"₹{metrics.get('max_drawdown', 0):,.2f}", 
            row
        )
        row += 1
        
        # Color code based on performance
        total_return = metrics.get('total_return_pct', 0)
        if total_return > 0:
            self.metric_labels['total_return'].setStyleSheet("font-size: 12px; color: #00FF00; font-weight: bold;")
            self.metric_labels['total_pnl'].setStyleSheet("font-size: 12px; color: #00FF00; font-weight: bold;")
        elif total_return < 0:
            self.metric_labels['total_return'].setStyleSheet("font-size: 12px; color: #FF6666; font-weight: bold;")
            self.metric_labels['total_pnl'].setStyleSheet("font-size: 12px; color: #FF6666; font-weight: bold;")
