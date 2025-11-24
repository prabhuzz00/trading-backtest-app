# Trading Backtest App

Cross-platform desktop application for backtesting trading strategies using PyQt6 and Python. It loads historical equity, stocks, and options data from MongoDB, allows users to add Python strategies and run backtests, then displays trades, equity curve and metrics.

## Features
- PyQt6 desktop UI (Windows/Linux)
- Dynamic user strategy loading (Python files)
- Backtesting engine using pandas/numpy
- MongoDB data connector (pymongo)
- Example moving-average strategy

## Quickstart
1. Clone the repo
2. Create and activate a virtualenv

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure MongoDB URI in `config/config.yaml`
4. Run the app

```bash
python src/main.py
```

## Packaging
Use PyInstaller to build executables for Windows/Linux.

## Contributing
Feel free to open issues and PRs.