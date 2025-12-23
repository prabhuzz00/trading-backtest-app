"""
Dark theme stylesheet for trading platform UI
"""

DARK_THEME = """
/* Main Window */
QMainWindow {
    background-color: #131722;
    color: #D1D4DC;
}

QWidget {
    background-color: #131722;
    color: #D1D4DC;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    font-size: 13px;
}

/* Toolbar */
QToolBar {
    background-color: #1E222D;
    border: none;
    spacing: 5px;
    padding: 5px;
}

QToolButton {
    background-color: transparent;
    color: #D1D4DC;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
}

QToolButton:hover {
    background-color: #2A2E39;
}

QToolButton:pressed {
    background-color: #363A45;
}

/* Sidebar Stock List */
QListWidget {
    background-color: #1E222D;
    color: #D1D4DC;
    border: none;
    border-right: 1px solid #2A2E39;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #2A2E39;
}

QListWidget::item:hover {
    background-color: #2A2E39;
}

QListWidget::item:selected {
    background-color: #2962FF;
    color: white;
}

/* Buttons */
QPushButton {
    background-color: #2962FF;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1E53E5;
}

QPushButton:pressed {
    background-color: #1848CC;
}

QPushButton:disabled {
    background-color: #2A2E39;
    color: #6A6D78;
}

QPushButton#secondaryButton {
    background-color: #2A2E39;
    color: #D1D4DC;
}

QPushButton#secondaryButton:hover {
    background-color: #363A45;
}

/* ComboBox */
QComboBox {
    background-color: #2A2E39;
    color: #D1D4DC;
    border: 1px solid #363A45;
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 150px;
}

QComboBox:hover {
    border-color: #2962FF;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #D1D4DC;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #2A2E39;
    color: #D1D4DC;
    selection-background-color: #2962FF;
    border: 1px solid #363A45;
}

/* Date Edit */
QDateEdit {
    background-color: #2A2E39;
    color: #D1D4DC;
    border: 1px solid #363A45;
    border-radius: 4px;
    padding: 6px 10px;
}

QDateEdit:hover {
    border-color: #2962FF;
}

QDateEdit::drop-down {
    border: none;
    padding-right: 10px;
}

QDateEdit::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #D1D4DC;
    margin-right: 5px;
}

QCalendarWidget {
    background-color: #2A2E39;
    color: #D1D4DC;
}

QCalendarWidget QToolButton {
    color: #D1D4DC;
    background-color: transparent;
}

QCalendarWidget QMenu {
    background-color: #2A2E39;
    color: #D1D4DC;
}

QCalendarWidget QSpinBox {
    background-color: #363A45;
    color: #D1D4DC;
    selection-background-color: #2962FF;
}

QCalendarWidget QAbstractItemView:enabled {
    background-color: #2A2E39;
    color: #D1D4DC;
    selection-background-color: #2962FF;
}

/* Labels */
QLabel {
    color: #D1D4DC;
    background-color: transparent;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
    color: #FFFFFF;
}

QLabel#stockPriceLabel {
    font-size: 24px;
    font-weight: bold;
    color: #FFFFFF;
}

QLabel#priceChangePositive {
    color: #26A69A;
    font-size: 14px;
}

QLabel#priceChangeNegative {
    color: #EF5350;
    font-size: 14px;
}

/* Tab Widget */
QTabWidget::pane {
    background-color: #131722;
    border: none;
}

QTabBar::tab {
    background-color: #1E222D;
    color: #787B86;
    padding: 10px 20px;
    border: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
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

/* Table */
QTableWidget {
    background-color: #1E222D;
    color: #D1D4DC;
    gridline-color: #2A2E39;
    border: none;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #2962FF;
    color: white;
}

QHeaderView::section {
    background-color: #2A2E39;
    color: #787B86;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #363A45;
    font-weight: 600;
}

/* Scrollbar */
QScrollBar:vertical {
    background-color: #1E222D;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #363A45;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #434651;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1E222D;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #363A45;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #434651;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Progress Bar */
QProgressBar {
    background-color: #2A2E39;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #D1D4DC;
}

QProgressBar::chunk {
    background-color: #2962FF;
    border-radius: 4px;
}

/* Status Bar */
QStatusBar {
    background-color: #1E222D;
    color: #787B86;
    border-top: 1px solid #2A2E39;
}

/* Line Edit */
QLineEdit {
    background-color: #2A2E39;
    color: #D1D4DC;
    border: 1px solid #363A45;
    border-radius: 4px;
    padding: 6px 10px;
}

QLineEdit:hover {
    border-color: #2962FF;
}

QLineEdit:focus {
    border-color: #2962FF;
}

/* Splitter */
QSplitter::handle {
    background-color: #2A2E39;
}

QSplitter::handle:hover {
    background-color: #363A45;
}

/* Menu */
QMenu {
    background-color: #2A2E39;
    color: #D1D4DC;
    border: 1px solid #363A45;
}

QMenu::item {
    padding: 8px 30px 8px 20px;
}

QMenu::item:selected {
    background-color: #2962FF;
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #363A45;
    margin: 4px 0;
}

/* Message Box */
QMessageBox {
    background-color: #2A2E39;
    color: #D1D4DC;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""
