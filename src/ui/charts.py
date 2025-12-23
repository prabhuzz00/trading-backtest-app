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
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create matplotlib figure with dark theme
        self.figure = Figure(figsize=(10, 6), facecolor='#131722')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #131722;")
        layout.addWidget(self.canvas)
        
        self.label = QLabel("Run a backtest to see the equity curve")
        self.label.setStyleSheet("color: #787B86; padding: 8px; background-color: #1E222D;")
        layout.addWidget(self.label)

    def plot_equity_curve(self, equity_curve):
        """
        Plot the equity curve from backtest results with dark theme.
        Optimized for large datasets with downsampling.
        
        Args:
            equity_curve: list of dicts {'date': datetime, 'equity': float}
        """
        if not equity_curve:
            self.label.setText("No equity data to plot")
            return
        
        # Clear previous plot efficiently
        self.figure.clear()
        
        # Downsample if dataset is very large (>5000 points)
        if len(equity_curve) > 5000:
            step = len(equity_curve) // 5000
            equity_curve = equity_curve[::step]
        
        # Create subplot with dark background
        ax = self.figure.add_subplot(111, facecolor='#1E222D')
        
        # Extract dates and equity values
        dates = [point['date'] for point in equity_curve]
        equity_values = [point['equity'] for point in equity_curve]
        
        # Plot equity curve with trading platform style
        ax.plot(dates, equity_values, linewidth=2, color='#2962FF', label='Portfolio Value', antialiased=True)
        
        # Fill area under curve
        ax.fill_between(dates, equity_values, alpha=0.1, color='#2962FF')
        
        # Format the plot with dark theme
        ax.set_xlabel('Date', fontsize=10, color='#787B86')
        ax.set_ylabel('Portfolio Value (₹)', fontsize=10, color='#787B86')
        ax.set_title('Equity Curve', fontsize=12, fontweight='bold', color='#D1D4DC', pad=15)
        ax.grid(True, alpha=0.1, linestyle='-', linewidth=0.5, color='#363A45')
        ax.legend(loc='best', framealpha=0.9, facecolor='#2A2E39', edgecolor='#363A45', 
                 labelcolor='#D1D4DC')
        
        # Style the spines
        for spine in ax.spines.values():
            spine.set_color('#363A45')
            spine.set_linewidth(0.5)
        
        # Style tick labels
        ax.tick_params(colors='#787B86', which='both')
        
        # Format x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()  # Rotate date labels
        
        # Tight layout to prevent label cutoff
        self.figure.tight_layout(pad=1.0)
        
        # Update the canvas with blit for faster rendering
        self.canvas.draw_idle()  # Use draw_idle instead of draw for better performance
        
        # Update status label
        initial_value = equity_values[0] if equity_values else 0
        final_value = equity_values[-1] if equity_values else 0
        pnl = final_value - initial_value
        pnl_pct = (pnl / initial_value * 100) if initial_value > 0 else 0
        
        color = "#26A69A" if pnl >= 0 else "#EF5350"
        self.label.setText(
            f"Equity points: {len(equity_curve)} | "
            f"Initial: ₹{initial_value:,.2f} | "
            f"Final: ₹{final_value:,.2f} | "
            f"<span style='color: {color};'>P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)</span>"
        )