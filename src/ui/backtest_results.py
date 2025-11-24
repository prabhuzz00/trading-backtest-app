from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem

class ResultsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)

    def display_results(self, results):
        trades = results.get("trades", [])
        self.table.clear()
        headers = ["date", "action", "symbol", "shares", "price"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(trades))
        for i, t in enumerate(trades):
            for j, h in enumerate(headers):
                self.table.setItem(i, j, QTableWidgetItem(str(t.get(h, ""))))