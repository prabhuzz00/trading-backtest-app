from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.label = QLabel("Run a backtest to see the equity curve")
        layout.addWidget(self.label)

    def plot_equity_curve(self, equity_curve):
        """
        Plot the equity curve from backtest results.
        
        Args:
            equity_curve: list of dicts {'date': datetime, 'equity': float}
        """
        if not equity_curve:
            self.label.setText("No equity data to plot")
            return
        
        # Clear previous plot
        self.figure.clear()
        
        # Create subplot
        ax = self.figure.add_subplot(111)
        
        # Extract dates and equity values
        dates = [point['date'] for point in equity_curve]
        equity_values = [point['equity'] for point in equity_curve]
        
        # Plot equity curve
        ax.plot(dates, equity_values, linewidth=2, color='#2E86AB', label='Portfolio Value')
        
        # Format the plot
        ax.set_xlabel('Date (IST)', fontsize=10)
        ax.set_ylabel('Portfolio Value (₹)', fontsize=10)
        ax.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()  # Rotate date labels
        
        # Tight layout to prevent label cutoff
        self.figure.tight_layout()
        
        # Update the canvas
        self.canvas.draw()
        
        # Update status label
        initial_value = equity_values[0] if equity_values else 0
        final_value = equity_values[-1] if equity_values else 0
        pnl = final_value - initial_value
        pnl_pct = (pnl / initial_value * 100) if initial_value > 0 else 0
        
        self.label.setText(
            f"Equity points: {len(equity_curve)} | "
            f"Initial: ₹{initial_value:,.2f} | "
            f"Final: ₹{final_value:,.2f} | "
            f"P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)"
        )