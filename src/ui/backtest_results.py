from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
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
        self.table.clear()
        
        # Updated headers to include value, P&L, and P&L%
        headers = ["Date", "Action", "Symbol", "Shares", "Price", "Value", "P&L", "P&L %"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(trades))
        
        for i, t in enumerate(trades):
            # Date
            date_item = QTableWidgetItem(str(t.get('date', '')))
            self.table.setItem(i, 0, date_item)
            
            # Action
            action = t.get('action', '')
            action_item = QTableWidgetItem(action)
            if action == 'BUY':
                action_item.setBackground(QColor(144, 238, 144))  # Light green
                action_item.setForeground(QColor(0, 100, 0))  # Dark green text
            elif action == 'SELL':
                action_item.setBackground(QColor(255, 160, 160))  # Light red
                action_item.setForeground(QColor(139, 0, 0))  # Dark red text
            self.table.setItem(i, 1, action_item)
            
            # Symbol
            symbol_item = QTableWidgetItem(str(t.get('symbol', '')))
            self.table.setItem(i, 2, symbol_item)
            
            # Shares
            shares_item = QTableWidgetItem(str(t.get('shares', '')))
            shares_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 3, shares_item)
            
            # Price
            price = t.get('price', 0)
            price_item = QTableWidgetItem(f"₹{price:,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 4, price_item)
            
            # Value
            value = t.get('value', 0)
            value_item = QTableWidgetItem(f"₹{value:,.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 5, value_item)
            
            # P&L (only for SELL trades)
            pnl = t.get('pnl', 0)
            if action == 'SELL':
                pnl_item = QTableWidgetItem(f"₹{pnl:,.2f}")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if pnl > 0:
                    pnl_item.setForeground(QColor(0, 150, 0))  # Bright green for profit
                    pnl_item.setBackground(QColor(200, 255, 200))  # Very light green
                elif pnl < 0:
                    pnl_item.setForeground(QColor(200, 0, 0))  # Bright red for loss
                    pnl_item.setBackground(QColor(255, 220, 220))  # Very light red
                self.table.setItem(i, 6, pnl_item)
            else:
                pnl_item = QTableWidgetItem("-")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 6, pnl_item)
            
            # P&L % (only for SELL trades)
            pnl_pct = t.get('pnl_pct', 0)
            if action == 'SELL':
                pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if pnl_pct > 0:
                    pnl_pct_item.setForeground(QColor(0, 150, 0))  # Bright green for profit
                    pnl_pct_item.setBackground(QColor(200, 255, 200))  # Very light green
                elif pnl_pct < 0:
                    pnl_pct_item.setForeground(QColor(200, 0, 0))  # Bright red for loss
                    pnl_pct_item.setBackground(QColor(255, 220, 220))  # Very light red
                self.table.setItem(i, 7, pnl_pct_item)
            else:
                pnl_pct_item = QTableWidgetItem("-")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 7, pnl_pct_item)
        
        # Resize columns to content
        self.table.resizeColumnsToContents()
