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
        scroll_area.setStyleSheet("background-color: #131722; border: none;")
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #131722;")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Backtest Summary")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px; color: #D1D4DC;")
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
    
    def create_metric_row(self, label_text, value_text, row, value_color="#D1D4DC"):
        """Create a row with label and value."""
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: 600; font-size: 13px; color: #787B86; padding: 5px;")
        label.setWordWrap(True)
        label.setMinimumWidth(150)
        
        value = QLabel(value_text)
        value.setStyleSheet(f"font-size: 14px; color: {value_color}; padding: 5px; font-weight: 500;")
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value.setWordWrap(True)
        value.setMinimumWidth(100)
        
        self.grid.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.grid.addWidget(value, row, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        return value
    
    def display_summary(self, results, symbol=None):
        """Display summary metrics from backtest results.
        
        Args:
            results: Backtest results dictionary
            symbol: Stock/instrument symbol (for detecting options trading)
        """
        # Clear existing widgets
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
        
        self.metric_labels.clear()
        
        metrics = results.get('metrics', {})
        
        if not metrics:
            no_data = QLabel("Run a backtest to see summary metrics")
            no_data.setStyleSheet("font-style: italic; color: #787B86; padding: 20px;")
            no_data.setWordWrap(True)
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(no_data, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
            return
        
        # Detect if this is options trading
        is_options = symbol and 'NSEFO' in symbol
        
        row = 0
        
        # Trading Type Indicator
        if is_options:
            type_label = QLabel("🎯 Options Strategy Backtest")
            type_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #42A5F5; padding-top: 5px; padding-bottom: 10px;")
        else:
            type_label = QLabel("📈 Equity Strategy Backtest")
            type_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #26A69A; padding-top: 5px; padding-bottom: 10px;")
        type_label.setWordWrap(True)
        self.grid.addWidget(type_label, row, 0, 1, 2)
        row += 1
        
        # Performance Metrics
        section_label = QLabel("📊 Performance Metrics")
        section_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #D1D4DC; padding-top: 10px; padding-bottom: 5px;")
        section_label.setWordWrap(True)
        self.grid.addWidget(section_label, row, 0, 1, 2)
        row += 1
        
        total_return = metrics.get('total_return_pct', 0)
        return_color = "#26A69A" if total_return >= 0 else "#EF5350"
        self.metric_labels['total_return'] = self.create_metric_row(
            "Total Return:", 
            f"{total_return:.2f}%", 
            row,
            return_color
        )
        row += 1
        
        total_pnl = metrics.get('total_pnl', 0)
        pnl_color = "#26A69A" if total_pnl >= 0 else "#EF5350" 
        self.metric_labels['total_pnl'] = self.create_metric_row(
            "Total P&L:", 
            f"₹{total_pnl:,.2f}", 
            row,
            pnl_color
        )
        row += 1
        
        self.metric_labels['total_brokerage'] = self.create_metric_row(
            "Total Brokerage:", 
            f"₹{metrics.get('total_brokerage', 0):,.2f}", 
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
        separator.setStyleSheet("background-color: #2A2E39;")
        self.grid.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Trade Statistics
        section_label = QLabel("📈 Trade Statistics")
        section_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #D1D4DC; padding-top: 10px; padding-bottom: 5px;")
        section_label.setWordWrap(True)
        self.grid.addWidget(section_label, row, 0, 1, 2)
        row += 1
        
        self.metric_labels['total_trades'] = self.create_metric_row(
            "Total Trades:", 
            str(metrics.get('total_trades', 0)), 
            row
        )
        row += 1
        
        self.metric_labels['total_long_trades'] = self.create_metric_row(
            "Long Trades:", 
            str(metrics.get('total_long_trades', 0)), 
            row
        )
        row += 1
        
        self.metric_labels['total_short_trades'] = self.create_metric_row(
            "Short Trades:", 
            str(metrics.get('total_short_trades', 0)), 
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
        separator.setStyleSheet("background-color: #2A2E39;")
        self.grid.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Profit/Loss Analysis
        section_label = QLabel("💰 Profit/Loss Analysis")
        section_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #D1D4DC; padding-top: 10px; padding-bottom: 5px;")
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
        separator.setStyleSheet("background-color: #2A2E39;")
        self.grid.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # Risk Metrics
        section_label = QLabel("⚠️ Risk Metrics")
        section_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #D1D4DC; padding-top: 10px; padding-bottom: 5px;")
        section_label.setWordWrap(True)
        self.grid.addWidget(section_label, row, 0, 1, 2)
        row += 1
        
        max_dd_pct = metrics.get('max_drawdown_pct', 0)
        dd_color = "#EF5350" if max_dd_pct < -10 else "#FFA726" if max_dd_pct < -5 else "#D1D4DC"
        self.metric_labels['max_drawdown'] = self.create_metric_row(
            "Max Drawdown:", 
            f"{max_dd_pct:.2f}%", 
            row,
            dd_color
        )
        row += 1
        
        self.metric_labels['max_drawdown_value'] = self.create_metric_row(
            "Max Drawdown Value:", 
            f"₹{metrics.get('max_drawdown', 0):,.2f}", 
            row,
            dd_color
        )
        row += 1        
        # Options-specific metrics (if applicable)
        if is_options:
            # Add separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("background-color: #2A2E39;")
            self.grid.addWidget(separator, row, 0, 1, 2)
            row += 1
            
            section_label = QLabel("📋 Options Strategy Metrics")
            section_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #42A5F5; padding-top: 10px; padding-bottom: 5px;")
            section_label.setWordWrap(True)
            self.grid.addWidget(section_label, row, 0, 1, 2)
            row += 1
            
            # Count trades with options info
            trades = results.get('trades', [])
            options_trades = sum(1 for t in trades if t.get('options_info'))
            
            self.metric_labels['options_trades'] = self.create_metric_row(
                "Options Positions:", 
                f"{options_trades // 2 if options_trades > 0 else 0} spreads", 
                row,
                "#42A5F5"
            )
            row += 1
            
            # Calculate average premium paid/received
            entry_trades = [t for t in trades if t.get('action') in ['BUY', 'BUY_LONG'] and t.get('options_info')]
            if entry_trades:
                avg_cost = sum(t.get('value', 0) for t in entry_trades) / len(entry_trades)
                self.metric_labels['avg_spread_cost'] = self.create_metric_row(
                    "Avg Spread Cost:", 
                    f"₹{avg_cost:,.2f}", 
                    row,
                    "#42A5F5"
                )
                row += 1
            
            # Win rate for options specifically
            exit_trades = [t for t in trades if t.get('action') in ['SELL', 'SELL_LONG'] and t.get('options_info')]
            if exit_trades:
                winning_options = sum(1 for t in exit_trades if t.get('pnl', 0) > 0)
                options_win_rate = (winning_options / len(exit_trades)) * 100 if exit_trades else 0
                wr_color = "#26A69A" if options_win_rate >= 50 else "#EF5350"
                self.metric_labels['options_win_rate'] = self.create_metric_row(
                    "Options Win Rate:", 
                    f"{options_win_rate:.1f}%", 
                    row,
                    wr_color
                )
                row += 1