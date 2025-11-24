from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
# Small stub for chart widget - replace with pyqtgraph or matplotlib integration
class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.label = QLabel("Equity curve will be plotted here")
        layout.addWidget(self.label)

    def plot_equity_curve(self, equity_curve):
        # equity_curve: list of dicts {'date':..., 'equity':...}
        # TODO: implement plotting using matplotlib or pyqtgraph
        self.label.setText(f"Equity points: {len(equity_curve)}")