"""
Stock Sidebar Widget - Left panel showing list of available stocks
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class StockListItem(QWidget):
    """Custom widget for displaying stock information in list"""
    def __init__(self, symbol, price, change_pct):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Symbol
        symbol_label = QLabel(symbol)
        symbol_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #D1D4DC;")
        layout.addWidget(symbol_label)
        
        # Price and change
        price_layout = QHBoxLayout()
        price_layout.setSpacing(8)
        
        price_label = QLabel(f"₹{price:,.2f}" if price else "")
        price_label.setStyleSheet("font-size: 12px; color: #D1D4DC;")
        price_layout.addWidget(price_label)
        
        if change_pct is not None:
            color = "#26A69A" if change_pct >= 0 else "#EF5350"
            sign = "+" if change_pct >= 0 else ""
            change_label = QLabel(f"{sign}{change_pct:.2f}%")
            change_label.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: 500;")
            price_layout.addWidget(change_label)
        
        price_layout.addStretch()
        layout.addLayout(price_layout)


class StockSidebar(QWidget):
    """Left sidebar showing available stocks for backtesting"""
    stock_selected = pyqtSignal(str)  # Emits stock symbol when selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.stocks_data = {}  # Store stock data: {symbol: {'price': float, 'change': float}}
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #1E222D; padding: 12px;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title = QLabel("INSTRUMENTS")
        title.setStyleSheet("font-size: 11px; font-weight: bold; color: #787B86;")
        header_layout.addWidget(title)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search symbols...")
        self.search_box.textChanged.connect(self.filter_stocks)
        header_layout.addWidget(self.search_box)
        
        layout.addWidget(header)
        
        # Stock list
        self.stock_list = QListWidget()
        self.stock_list.setStyleSheet("""
            QListWidget {
                background-color: #1E222D;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #2A2E39;
                padding: 0;
            }
            QListWidget::item:hover {
                background-color: #2A2E39;
            }
            QListWidget::item:selected {
                background-color: #2962FF;
            }
        """)
        self.stock_list.itemClicked.connect(self.on_stock_clicked)
        layout.addWidget(self.stock_list)
        
        # Footer with count
        self.footer_label = QLabel("0 symbols")
        self.footer_label.setStyleSheet("""
            background-color: #1E222D; 
            color: #787B86; 
            padding: 8px 12px;
            font-size: 11px;
            border-top: 1px solid #2A2E39;
        """)
        layout.addWidget(self.footer_label)
    
    def set_stocks(self, stocks_list):
        """
        Set the list of available stocks
        Args:
            stocks_list: list of stock symbols or list of dicts with stock info
        """
        self.stock_list.clear()
        self.stocks_data = {}
        
        for stock in stocks_list:
            if isinstance(stock, dict):
                symbol = stock.get('symbol', '')
                price = stock.get('price', None)
                change_pct = stock.get('change_pct', None)
            else:
                symbol = stock
                price = None
                change_pct = None
            
            self.stocks_data[symbol] = {
                'price': price,
                'change': change_pct
            }
            
            # Create list item
            item = QListWidgetItem(self.stock_list)
            item.setData(Qt.ItemDataRole.UserRole, symbol)
            
            # Create custom widget
            widget = StockListItem(symbol, price, change_pct)
            item.setSizeHint(widget.sizeHint())
            
            self.stock_list.addItem(item)
            self.stock_list.setItemWidget(item, widget)
        
        self.update_footer()
    
    def filter_stocks(self, text):
        """Filter stocks based on search text"""
        search_text = text.lower()
        visible_count = 0
        
        for i in range(self.stock_list.count()):
            item = self.stock_list.item(i)
            symbol = item.data(Qt.ItemDataRole.UserRole)
            
            if search_text in symbol.lower():
                item.setHidden(False)
                visible_count += 1
            else:
                item.setHidden(True)
        
        self.footer_label.setText(f"{visible_count} symbols")
    
    def update_footer(self):
        """Update footer with stock count"""
        count = self.stock_list.count()
        self.footer_label.setText(f"{count} symbols")
    
    def on_stock_clicked(self, item):
        """Handle stock selection"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        self.stock_selected.emit(symbol)
    
    def get_selected_stock(self):
        """Get currently selected stock symbol"""
        current_item = self.stock_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def select_stock(self, symbol):
        """Programmatically select a stock by symbol"""
        for i in range(self.stock_list.count()):
            item = self.stock_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == symbol:
                self.stock_list.setCurrentItem(item)
                return True
        return False
