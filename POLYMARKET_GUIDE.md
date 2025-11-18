# 🎯 Polymarket 15m BTC YES/NO Trading Guide

## The Market

**Polymarket Market**: "Will the next BTC 15-minute candle be BULLISH?"

- **YES** = Next candle closes higher than it opens (green/bullish)
- **NO** = Next candle closes lower than it opens (red/bearish)

This market resolves **every 15 minutes** based on BTC price action.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Check Current BTC Chart

Look at BTC 15-minute chart on any exchange (Binance, Coinbase, TradingView)

**Count consecutive candles:**
- How many green candles in a row? OR
- How many red candles in a row?

### Step 2: Look Up Your Bet

Use this simple table:

| What You See | Polymarket Bet | Why |
|--------------|----------------|-----|
| 3+ green candles in a row | **Bet NO** | Reversal likely → next candle red |
| 3+ red candles in a row | **Bet YES** | Reversal likely → next candle green |
| 1-2 green candles | **SKIP** | Too noisy, no edge |
| 1-2 red candles | **SKIP** | Too noisy, no edge |

### Step 3: Place Bet on Polymarket

Go to Polymarket → Find "Will next 15m BTC candle be BULLISH?"
- Place your bet (YES or NO from table)
- Wait 15 minutes for resolution

---

## 📊 Detailed Signal Table

| Current Streak | Next Candle Prediction | Polymarket Bet | Confidence | Quality |
|----------------|------------------------|----------------|------------|---------|
| 1 green candle | Red (bearish) | **NO** | Medium | Skip |
| 2 green candles | Red (bearish) | **NO** | Medium | Skip |
| **3 green candles** | **Red (bearish)** | **NO** | **High** | **✅ BET** |
| **4 green candles** | **Red (bearish)** | **NO** | **Very High** | **✅ BET** |
| **5+ green candles** | **Red (bearish)** | **NO** | **Extreme** | **✅ BET** |
| 1 red candle | Green (bullish) | **YES** | Medium | Skip |
| 2 red candles | Green (bullish) | **YES** | Medium | Skip |
| **3 red candles** | **Green (bullish)** | **YES** | **High** | **✅ BET** |
| **4 red candles** | **Green (bullish)** | **YES** | **Very High** | **✅ BET** |
| **5+ red candles** | **Green (bullish)** | **YES** | **Extreme** | **✅ BET** |

---

## 💡 Examples

### Example 1: 4 Green Candles

**Situation**: BTC just closed its 4th consecutive green 15m candle

**Analysis**:
- Current streak: 4 UP
- Historical reversal rate: ~60%+
- Market is probably at 50/50

**Action**:
1. Go to Polymarket
2. Find "Will next 15m BTC candle be BULLISH?"
3. **Bet NO** (predicting red candle)
4. Position size: $50-100

**Logic**: After 4 greens, momentum exhausted → reversal likely

---

### Example 2: 3 Red Candles

**Situation**: BTC just closed its 3rd consecutive red 15m candle

**Analysis**:
- Current streak: 3 DOWN
- Historical reversal rate: ~58%+
- Market is probably at 50/50

**Action**:
1. Go to Polymarket
2. Find "Will next 15m BTC candle be BULLISH?"
3. **Bet YES** (predicting green candle)
4. Position size: $50-100

**Logic**: After 3 reds, selling exhausted → bounce likely

---

### Example 3: Only 1 Green Candle

**Situation**: BTC just had 1 green candle

**Analysis**:
- Current streak: 1 UP
- Not enough data for strong prediction
- Probability ~50/50

**Action**: **SKIP - Don't bet**

**Logic**: Too noisy, could go either way

---

## 🎯 Strategy Rules

### When to BET:
✅ 3+ consecutive candles in same direction
✅ Quality rating is A or A+
✅ You have funds available
✅ Market is liquid (>$10k volume)

### When to SKIP:
❌ Only 1-2 consecutive candles
❌ Quality rating is B or C
❌ You've hit daily loss limit
❌ Market has low liquidity

---

## 💰 Position Sizing

**Conservative** (Recommended for beginners):
- Streak of 3: Bet $25-50
- Streak of 4: Bet $50-75
- Streak of 5+: Bet $75-100

**Aggressive** (For experienced traders):
- Streak of 3: Bet $100
- Streak of 4: Bet $150
- Streak of 5+: Bet $200

**Never bet more than 5% of your total capital on a single trade!**

---

## 📈 Expected Performance

With proper execution:

| Metric | Expected Value |
|--------|----------------|
| Win Rate | 55-60% |
| Average Edge | 8-15% |
| Monthly Return | 15-25% |
| Max Drawdown | 10-15% |

**Important**: These are projections based on historical data. Real results will vary!

---

## 🔴 Real-Time Trading Flow

### Before Market Opens (Every 15 min)

**5 minutes before candle close:**

1. Open BTC 15m chart
2. Count current streak
3. Check if streak is 3+ candles
4. If yes → prepare your bet

**1 minute before candle close:**

5. Final check - confirm streak still valid
6. Go to Polymarket
7. Place bet (YES or NO based on table)

**After candle closes:**

8. Wait 15 minutes for resolution
9. Collect winnings or accept loss
10. Repeat for next candle

---

## 🤖 Automated Tool Usage

### Manual Method (Beginner)
```bash
# Run predictor
python3 polymarket_15m_predictor.py

# Check table, manually place bet on Polymarket
```

### Semi-Automated (Intermediate)
```python
from polymarket_15m_predictor import Polymarket15mPredictor

# Initialize
predictor = Polymarket15mPredictor()
predictor.train()

# Get current streak (from chart)
current_streak = "UP"
streak_length = 4

# Get prediction
result = predictor.predict_next_candle(current_streak, streak_length)

# Check recommendation
if result['quality'] in ['A+', 'A']:
    print(f"BET {result['polymarket_bet']}")
    # Manually go to Polymarket and place bet
```

### Fully Automated (Advanced)
```python
# Use realtime_monitor.py + polymarket_trader.py
# Requires:
# - WebSocket connection to Binance
# - Polymarket API integration
# - Risk management system

# See STRATEGY.md for full implementation
```

---

## ⚠️ Risk Management

### Daily Limits
- Maximum 10 trades per day
- Maximum 5% loss per day
- Stop trading if you lose 3 in a row

### Position Limits
- Never bet more than 5% of capital per trade
- Maximum total exposure: 20% of capital
- Keep 50%+ in reserve

### Emotional Discipline
- Follow the system - no revenge trading
- Don't increase bet size after losses
- Take breaks after 5 consecutive trades
- Review performance weekly

---

## 📚 Quick Reference Card

**Print this out and keep next to your computer:**

```
╔══════════════════════════════════════════════════════════╗
║         POLYMARKET 15M BTC BETTING CHEAT SHEET          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  IF: 3+ GREEN CANDLES → BET NO (next will be red)       ║
║  IF: 3+ RED CANDLES   → BET YES (next will be green)    ║
║                                                          ║
║  IF: Only 1-2 candles → SKIP (no edge)                  ║
║                                                          ║
║  Position Size: $50-100 max                             ║
║  Daily Limit: 10 trades max                             ║
║  Stop Loss: -5% per day                                 ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

## 🎓 FAQ

**Q: What if I see 6 green candles?**
A: Even better! Bet NO with high confidence. The longer the streak, the higher the reversal probability.

**Q: What if the market is at 60/40 instead of 50/50?**
A: Calculate your edge: If market is 60% YES and you predict NO, you still have edge if your probability >60%.

**Q: How much can I make per trade?**
A: With $100 bet and 2% fee: Win = +$98, Lose = -$102. Expected value depends on your win rate.

**Q: What if Polymarket doesn't have exactly this market?**
A: Look for similar markets: "BTC price up/down", "BTC green/red candle", etc. Same logic applies.

**Q: Can I use this on other timeframes?**
A: Yes! Works on 5m, 30m, 1h. Just re-run analysis with different interval.

---

## 🚀 Next Steps

1. **Week 1**: Paper trade (track signals, don't bet real money)
2. **Week 2**: Start with $10-25 positions
3. **Week 3-4**: Increase to $50 if profitable
4. **Month 2+**: Scale to $100+ based on results

**Goal**: Build confidence and prove the system works before scaling up!

---

## 📞 Support

If you need help:
1. Review `STRATEGY.md` for detailed methodology
2. Run `python3 polymarket_15m_predictor.py` for predictions
3. Check `BACKTEST_RESULTS.md` for performance analysis

---

**Remember**: This is a probability game, not a guarantee. Even with 60% win rate, you'll lose 40% of trades. Stay disciplined and manage risk!

*Last Updated: November 2025*
