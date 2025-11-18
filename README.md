# 🎯 BTC Streak Prediction System for Polymarket

**Quantitative trading system for predicting BTC candle direction reversals using statistical streak analysis**

Built with Python • Statistical Analysis • Real-Time Monitoring • Automated Trading

---

## 📊 Overview

This system analyzes Bitcoin 15-minute candle patterns to identify high-probability reversal opportunities. It uses rigorous statistical methods including confidence intervals, hypothesis testing, and Kelly Criterion position sizing to generate trading signals for Polymarket prediction markets.

### Key Features

✅ **Statistical Analysis Engine**
- Fetches 90 days of BTC historical data
- Calculates streak probabilities with 95% confidence intervals
- Identifies edges using Wilson score intervals
- Filters signals by minimum edge and statistical significance

✅ **Backtesting Framework**
- Realistic transaction cost modeling (Polymarket fees)
- Performance metrics: Sharpe ratio, max drawdown, profit factor
- Trade-by-trade analysis by streak length
- CSV export for further analysis

✅ **Real-Time Monitoring**
- WebSocket connection to Binance for live data
- Automatic streak detection on new candles
- Configurable signal callbacks for alerts
- Thread-safe concurrent processing

✅ **Polymarket Integration**
- Kelly Criterion position sizing
- Risk management (daily loss limits, max position size)
- Order simulation framework
- Full setup guide for production trading

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd polymarketbtc

# Install dependencies
pip install -r requirements.txt
```

### Run Analysis

```bash
# 1. Statistical Analysis
python btc_streak_analysis.py

# 2. Backtesting
python backtester.py

# 3. Real-Time Monitor (requires active internet)
python realtime_monitor.py

# 4. Polymarket Trader Demo
python polymarket_trader.py
```

---

## 📁 Project Structure

```
polymarketbtc/
├── btc_streak_analysis.py    # Core statistical analysis engine
├── backtester.py              # Backtesting framework
├── realtime_monitor.py        # Live WebSocket monitoring
├── polymarket_trader.py       # Trading logic & risk management
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── backtest_results.csv       # Generated after backtest run
```

---

## 🧪 How It Works

### 1. Statistical Analysis

The system analyzes consecutive same-direction candles (streaks) and calculates:

- **Streak Distribution**: How often do we see 1, 2, 3+ consecutive UP/DOWN candles?
- **Reversal Probability**: After N consecutive candles, what's the probability of reversal?
- **Confidence Intervals**: 95% Wilson score intervals for statistical rigor
- **Edge Calculation**: Our probability - market probability

**Example Output:**
```
direction  streak_length  reversal_prob  ci_lower  ci_upper  sample_size  edge
UP         3              0.58           0.52      0.64      252          0.08
DOWN       4              0.62           0.54      0.70      160          0.12
```

### 2. Signal Generation

Signals are generated when:
- Streak length matches historical pattern
- Edge > 10% (configurable)
- Confidence interval is tight (ci_lower > 0.55)
- Sufficient sample size (n ≥ 10)

### 3. Position Sizing

Uses **fractional Kelly Criterion** for conservative sizing:

```python
kelly = (probability - market_price) / (1 - market_price)
position_size = max_position * kelly * kelly_fraction  # Default: 0.25
```

### 4. Risk Management

Multiple layers of protection:
- Maximum position size per trade
- Daily loss limits
- Maximum trades per day
- Minimum edge requirements
- Real-time P&L tracking

---

## 📈 Backtest Results

**Sample Performance (Synthetic Data):**

```
Total Trades:        8564
Win Rate:           48.48%
Total Return:       -89.60%
Sharpe Ratio:       -9.38
Max Drawdown:       -90.19%
Profit Factor:      0.89
```

⚠️ **Note**: The poor performance on synthetic data demonstrates the importance of:
1. Transaction costs (4% round-trip kills edge)
2. Real market data (synthetic data has unrealistic patterns)
3. Proper signal filtering

**With real data and optimized parameters, target metrics:**
- Win Rate: 55-60%
- Sharpe Ratio: >1.5
- Max Drawdown: <20%
- Profit Factor: >1.5

---

## 🔴 Real-Time Monitoring

The real-time monitor connects to Binance WebSocket and:

1. Maintains rolling buffer of recent candles
2. Detects streak patterns as they form
3. Generates signals when patterns match
4. Calls callback function for automated action

**Usage:**

```python
from realtime_monitor import RealtimeBTCMonitor

def my_signal_handler(signal):
    print(f"Signal: {signal}")
    # Place Polymarket bet
    # Send Telegram notification
    # Log to database

monitor = RealtimeBTCMonitor(
    interval='15m',
    lookback=20,
    signal_callback=my_signal_handler
)

monitor.start()
```

---

## 💰 Polymarket Integration

### Setup Steps

1. **Create Account**
   - Sign up at https://polymarket.com
   - Complete KYC verification
   - Fund with USDC on Polygon network

2. **API Access**
   - Request API credentials
   - Store securely in `.env` file

3. **Install SDK**
   ```bash
   pip install py-clob-client web3
   ```

4. **Configure**
   ```bash
   # .env file
   POLYMARKET_API_KEY=your_key
   POLYMARKET_PRIVATE_KEY=your_private_key
   ```

5. **Test in Simulation Mode**
   ```bash
   python polymarket_trader.py
   ```

### Production Trading

⚠️ **WARNING**: Start small and test thoroughly!

- Begin with $10-50 position sizes
- Monitor for 1-2 weeks before scaling
- Check market liquidity (>$10k volume)
- Be aware of gas fees on Polygon
- Never risk more than you can afford to lose

---

## 🧠 Quantitative Insights

### Why Streak Analysis Works

1. **Mean Reversion**: Markets tend to revert after extreme moves
2. **Momentum Exhaustion**: Extended trends lose steam
3. **Psychological Levels**: Traders react to patterns
4. **Statistical Edge**: Historical probabilities ≠ market prices

### Limitations

- **Data Mining Bias**: Patterns may not persist
- **Regime Changes**: Market behavior evolves
- **Liquidity**: Polymarket markets may have limited size
- **Latency**: WebSocket delays can affect execution
- **Fees**: Transaction costs erode edge quickly

### Best Practices

✅ Always use confidence intervals
✅ Require minimum sample sizes (n ≥ 10)
✅ Apply conservative position sizing
✅ Monitor live performance vs backtest
✅ Re-calibrate strategy monthly
✅ Maintain detailed trade logs

---

## 🛠️ Advanced Usage

### Custom Signal Rules

Edit `realtime_monitor.py` to customize:

```python
self.signal_rules = [
    {
        "streak_length": 5,
        "direction": "UP",
        "action": "BET_REVERSAL",
        "prediction": "DOWN",
        "min_prob": 0.70  # Higher threshold
    }
]
```

### Different Timeframes

Change interval in any script:

```python
analyzer = BTCStreakAnalyzer(interval='5m', lookback_days=30)
monitor = RealtimeBTCMonitor(interval='1h')
```

### Alternative Data Sources

Replace Binance API with:
- CoinGecko
- Kraken
- Coinbase Pro
- Your own data pipeline

---

## 📚 Dependencies

```
pandas>=2.0.0         # Data manipulation
numpy>=1.24.0         # Numerical computing
scipy>=1.11.0         # Statistical functions
requests>=2.31.0      # HTTP requests
websocket-client      # Real-time data
python-dotenv         # Environment variables
```

---

## 🤝 Contributing

Improvements welcome! Areas for enhancement:

- [ ] Multi-timeframe analysis
- [ ] Machine learning integration
- [ ] Telegram bot notifications
- [ ] Dashboard/UI for monitoring
- [ ] Database integration
- [ ] Additional exchanges
- [ ] More sophisticated risk models

---

## ⚖️ Disclaimer

This software is for educational and research purposes only. Cryptocurrency trading and prediction markets involve substantial risk of loss. Past performance does not guarantee future results. The authors are not responsible for any financial losses incurred through use of this system.

**Key Risks:**
- Market risk (prices can move against you)
- Liquidity risk (inability to exit positions)
- Technical risk (bugs, API failures, WebSocket disconnections)
- Regulatory risk (prediction markets may be restricted in your jurisdiction)
- Counterparty risk (platform solvency)

Always do your own research and never risk money you cannot afford to lose.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support

For questions or issues:
- Open a GitHub issue
- Review Polymarket documentation
- Join Polymarket Discord community

---

**Built with ❤️ by quantitative traders, for quantitative traders**

*Last Updated: November 2025*
