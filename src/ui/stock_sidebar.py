"""
Stock Sidebar Widget - Left panel showing list of available stocks, futures, and options
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QLineEdit, QHBoxLayout, QPushButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class StockListItem(QWidget):
    """Custom widget for displaying stock/instrument information in list"""
    def __init__(self, symbol, price=None, change_pct=None, inst_type=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Top row: Symbol and badge
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)
        
        # Symbol
        symbol_label = QLabel(symbol)
        symbol_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #D1D4DC;")
        top_layout.addWidget(symbol_label)
        
        # Instrument type badge
        if inst_type:
            badge_colors = {
                'EQ': '#2962FF',    # Blue for stocks
                'FUT': '#FF6D00',   # Orange for futures
                'OPT': '#AB47BC'    # Purple for options
            }
            badge_color = badge_colors.get(inst_type, '#787B86')
            badge = QLabel(inst_type)
            badge.setStyleSheet(f"""
                background-color: {badge_color};
                color: white;
                font-size: 9px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 3px;
            """)
            top_layout.addWidget(badge)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Price and change
        if price is not None or change_pct is not None:
            price_layout = QHBoxLayout()
            price_layout.setSpacing(8)
            
            if price:
                price_label = QLabel(f"₹{price:,.2f}")
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
    """Left sidebar showing available instruments (stocks, futures, options) for backtesting"""
    stock_selected = pyqtSignal(str)  # Emits symbol when selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stocks_data = {}  # Store instrument data
        self.current_filter = 'ALL'  # Current filter: ALL, EQ, FUT, OPT
        self.setup_ui()
    
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
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)
        
        self.filter_buttons = {}
        self.filter_group = QButtonGroup()
        
        filters = [
            ('ALL', 'All', '#787B86'),
            ('EQ', 'Stocks', '#2962FF'),
            ('FUT', 'Futures', '#FF6D00'),
            ('OPT', 'Options', '#AB47BC')
        ]
        
        for filter_id, label, color in filters:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #787B86;
                    border: 1px solid #2A2E39;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }}
                QPushButton:checked {{
                    background-color: {color};
                    color: white;
                    border: 1px solid {color};
                }}
                QPushButton:hover {{
                    background-color: #2A2E39;
                }}
            """)
            btn.clicked.connect(lambda checked, fid=filter_id: self.set_filter(fid))
            self.filter_buttons[filter_id] = btn
            self.filter_group.addButton(btn)
            filter_layout.addWidget(btn)
        
        # Set ALL as default
        self.filter_buttons['ALL'].setChecked(True)
        
        header_layout.addLayout(filter_layout)
        
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
        Set the list of available instruments (stocks, futures, options)
        Args:
            stocks_list: list of stock symbols or list of dicts with stock/instrument info
        """
        self.stock_list.clear()
        self.stocks_data = {}
        
        for stock in stocks_list:
            if isinstance(stock, dict):
                symbol = stock.get('symbol', '')
                price = stock.get('price', None)
                change_pct = stock.get('change_pct', None)
                inst_type = stock.get('type', None)
            else:
                symbol = stock
                price = None
                change_pct = None
                inst_type = None
            
            self.stocks_data[symbol] = {
                'price': price,
                'change': change_pct,
                'type': inst_type
            }
            
            # Create list item
            item = QListWidgetItem(self.stock_list)
            item.setData(Qt.ItemDataRole.UserRole, symbol)
            
            # Create custom widget
            widget = StockListItem(symbol, price, change_pct, inst_type)
            item.setSizeHint(widget.sizeHint())
            
            self.stock_list.addItem(item)
            self.stock_list.setItemWidget(item, widget)
        
        self.update_footer()
    
    def filter_stocks(self, text=None):
        """Filter instruments based on search text and selected type filter"""
        if text is None:
            text = self.search_box.text()
        
        search_text = text.lower()
        visible_count = 0
        
        for i in range(self.stock_list.count()):
            item = self.stock_list.item(i)
            symbol = item.data(Qt.ItemDataRole.UserRole)
            
            # Check search text match
            text_match = search_text in symbol.lower()
            
            # Check instrument type filter
            inst_data = self.stocks_data.get(symbol, {})
            inst_type = inst_data.get('type', '')
            
            type_match = (self.current_filter == 'ALL' or 
                         self.current_filter == inst_type)
            
            if text_match and type_match:
                item.setHidden(False)
                visible_count += 1
            else:
                item.setHidden(True)
        
        self.footer_label.setText(f"{visible_count} symbols")
    
    def set_filter(self, filter_type):
        """Set the instrument type filter"""
        self.current_filter = filter_type
        self.filter_stocks()
    
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
