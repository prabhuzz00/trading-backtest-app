from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class ResultsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def display_results(self, results):
        trades = results.get("trades", [])
        
        # Disable sorting and updates for faster rendering
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(False)
        
        # Block signals during population
        self.table.blockSignals(True)
        
        self.table.clear()
        
        # Updated headers to include Type column and Options Info
        headers = ["Date", "Action", "Type", "Symbol", "Shares", "Price", "Value", "Brokerage", "P&L", "P&L %", "Options Info"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(trades))
        
        # Pre-create color objects to avoid repeated allocations
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
        
        # Batch render rows for better performance
        for i, t in enumerate(trades):
            # Date
            date_item = QTableWidgetItem(str(t.get('date', '')))
            self.table.setItem(i, 0, date_item)
            
            # Action
            action = t.get('action', '')
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
            self.table.setItem(i, 1, action_item)
            
            # Trade Type
            trade_type = t.get('trade_type', 'LONG')
            type_item = QTableWidgetItem(trade_type)
            if trade_type == 'LONG':
                type_item.setForeground(dark_green)
            else:
                type_item.setForeground(orange)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, type_item)
            
            # Symbol
            symbol_item = QTableWidgetItem(str(t.get('symbol', '')))
            self.table.setItem(i, 3, symbol_item)
            
            # Shares
            shares_item = QTableWidgetItem(str(t.get('shares', '')))
            shares_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 4, shares_item)
            
            # Price
            price = t.get('price', 0)
            price_item = QTableWidgetItem(f"₹{price:,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 5, price_item)
            
            # Value
            value = t.get('value', 0)
            value_item = QTableWidgetItem(f"₹{value:,.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 6, value_item)
            
            # Brokerage
            brokerage = t.get('brokerage', 0)
            if action in ['SELL', 'SELL_LONG', 'BUY_SHORT']:
                total_brokerage = t.get('total_brokerage', brokerage)
                brokerage_item = QTableWidgetItem(f"₹{total_brokerage:,.2f}")
            else:
                brokerage_item = QTableWidgetItem(f"₹{brokerage:,.2f}")
            brokerage_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            brokerage_item.setForeground(orange)
            self.table.setItem(i, 7, brokerage_item)
            
            # P&L (only for closing trades)
            pnl = t.get('pnl', 0)
            if action in ['SELL', 'SELL_LONG', 'BUY_SHORT']:
                pnl_item = QTableWidgetItem(f"₹{pnl:,.2f}")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if pnl > 0:
                    pnl_item.setForeground(bright_green)
                    pnl_item.setBackground(very_light_green)
                elif pnl < 0:
                    pnl_item.setForeground(bright_red)
                    pnl_item.setBackground(very_light_red)
                self.table.setItem(i, 8, pnl_item)
            else:
                pnl_item = QTableWidgetItem("-")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 8, pnl_item)
            
            # P&L % (only for closing trades)
            pnl_pct = t.get('pnl_pct', 0)
            if action in ['SELL', 'SELL_LONG', 'BUY_SHORT']:
                pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if pnl_pct > 0:
                    pnl_pct_item.setForeground(bright_green)
                    pnl_pct_item.setBackground(very_light_green)
                elif pnl_pct < 0:
                    pnl_pct_item.setForeground(bright_red)
                    pnl_pct_item.setBackground(very_light_red)
                self.table.setItem(i, 9, pnl_pct_item)
            else:
                pnl_pct_item = QTableWidgetItem("-")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 9, pnl_pct_item)
            
            # Options Info (if available)
            options_info = t.get('options_info', '')
            if options_info:
                options_item = QTableWidgetItem(options_info)
                options_item.setForeground(QColor(100, 150, 255))
                self.table.setItem(i, 10, options_item)
            else:
                options_item = QTableWidgetItem("-")
                options_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 10, options_item)
        
        # Re-enable signals and updates
        self.table.blockSignals(False)
        
        # Resize columns to content once at end
        self.table.resizeColumnsToContents()
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
        
        # Re-enable updates and refresh
        self.table.setUpdatesEnabled(True)
        
        # Ensure table is visible and scrollable
        self.table.setVisible(True)
        self.table.scrollToTop()

