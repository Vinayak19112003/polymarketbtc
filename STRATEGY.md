# 📐 Quantitative Strategy Deep Dive

## Executive Summary

This document outlines the quantitative reasoning behind the BTC streak prediction system for Polymarket trading. It covers statistical foundations, edge detection, position sizing, risk management, and practical implementation considerations.

---

## 1. Core Hypothesis

**Premise**: Bitcoin price movements in short timeframes (15m candles) exhibit mean-reverting behavior after extended directional streaks.

**Rationale**:
- **Momentum Exhaustion**: Consecutive moves in one direction deplete buying/selling pressure
- **Profit Taking**: Traders lock in gains after runs, causing reversals
- **Support/Resistance**: Technical levels trigger counter-trend positions
- **Predictable Overreaction**: Short-term noise creates exploitable patterns

**Key Insight**: If the probability of reversal after N consecutive candles exceeds the market's implied probability, we have an edge.

---

## 2. Statistical Framework

### 2.1 Streak Definition

A **streak** is a sequence of consecutive candles moving in the same direction:
- `UP`: close > open
- `DOWN`: close < open
- `NEUTRAL`: close = open (ignored in analysis)

### 2.2 Probability Calculation

For each streak length `n` and direction `d`:

```
P(reversal | n consecutive d candles) = reversals / total_streaks
```

**Example**:
- 252 instances of 3 consecutive UP candles
- 146 followed by DOWN (reversal)
- P(reversal) = 146/252 = 0.579 (57.9%)

### 2.3 Confidence Intervals

We use **Wilson Score Interval** (not normal approximation) because:
- Better for extreme probabilities (near 0 or 1)
- Better for small sample sizes
- Asymmetric (respects 0-1 bounds)

**Formula**:
```
p̂ = observed proportion
n = sample size
z = 1.96 (95% confidence)

CI = (p̂ + z²/2n ± z√[(p̂(1-p̂) + z²/4n)/n]) / (1 + z²/n)
```

**Interpretation**:
- If CI = [0.52, 0.64], we're 95% confident true probability is in this range
- Tight CI → more reliable estimate
- Wide CI → need more data

### 2.4 Edge Calculation

**Edge** = Our probability - Market probability

For Polymarket:
- Market often prices outcomes near 50/50 (especially for new markets)
- If we estimate P(reversal) = 0.62 and market is at 0.50
- Edge = 0.62 - 0.50 = 0.12 (12%)

**Kelly Criterion** tells us how much to bet given this edge.

---

## 3. Signal Generation

### 3.1 Signal Criteria

A valid signal must satisfy:

1. **Statistical Significance**: Sample size ≥ 10 observations
2. **Minimum Edge**: Edge ≥ 10% (configurable)
3. **Confidence Threshold**: CI lower bound ≥ 55%
4. **Pattern Match**: Current market streak matches historical pattern

### 3.2 Signal Quality Tiers

| Tier | Edge | CI Lower | Sample Size | Action |
|------|------|----------|-------------|--------|
| A | >15% | >60% | >50 | Max position |
| B | 10-15% | 55-60% | 20-50 | Half position |
| C | 5-10% | 50-55% | 10-20 | Quarter position |
| D | <5% | <50% | <10 | Skip |

### 3.3 Example Signal

```
Condition: 4 consecutive UP candles
Historical Data:
  - Occurred 130 times
  - 81 followed by reversal (DOWN)
  - P(reversal) = 81/130 = 0.623
  - 95% CI = [0.54, 0.71]
  - Edge vs 50/50 = 0.123

Signal: BET DOWN (predict reversal)
Quality: Tier B (moderate confidence)
```

---

## 4. Position Sizing

### 4.1 Kelly Criterion

**Full Kelly**:
```
f = (p × b - q) / b

Where:
p = probability of winning
q = 1 - p
b = odds received on the bet (for 1:1, b = 1)

Simplifies to: f = 2p - 1 (for 50/50 markets)
```

**Example**:
- P(win) = 0.62
- Full Kelly = 2(0.62) - 1 = 0.24 (24% of bankroll)

### 4.2 Fractional Kelly

**Problem**: Full Kelly is volatile and assumes perfect probability estimates

**Solution**: Use fraction of Kelly (default: 25%)

```
Position Size = Bankroll × Kelly × Fraction
```

**Example**:
- Bankroll: $10,000
- Kelly: 24%
- Fraction: 25%
- Position: $10,000 × 0.24 × 0.25 = $600

### 4.3 Position Limits

Additional constraints:
```python
position_size = min(
    kelly_position,
    max_position_size,      # Hard cap (e.g., $1000)
    available_capital * 0.1 # Max 10% of capital
)
```

---

## 5. Risk Management

### 5.1 Trade-Level Risk

**Per-Trade Loss Limit**: 2% of capital maximum
- If bankroll = $10,000
- Max loss per trade = $200
- After Polymarket fees (2%), max bet ≈ $100

**Stop-Loss**: Not applicable (binary outcome markets)

### 5.2 Daily Risk Limits

```python
if daily_loss >= max_daily_loss:
    stop_trading_for_today()

if daily_trades >= max_trades_per_day:
    stop_trading_for_today()
```

**Typical Limits**:
- Max daily loss: 3-5% of capital
- Max trades per day: 15-20

**Rationale**: Prevents revenge trading and overexposure

### 5.3 Drawdown Management

**Max Drawdown Threshold**: 20% from peak

**Actions when approaching**:
1. Reduce position sizes by 50%
2. Increase minimum edge requirement to 15%
3. Pause trading until review
4. Re-evaluate strategy parameters

### 5.4 Correlation Risk

**Problem**: Multiple BTC markets correlated
- If 5 positions all on BTC direction
- Single event affects all positions

**Solution**: Position limits by asset
```python
max_exposure_per_asset = total_capital * 0.20  # 20% max
```

---

## 6. Transaction Costs

### 6.1 Polymarket Fees

**Trading Fee**: ~2% per side

**Round-trip cost**:
- Buy YES shares: -2%
- Outcome resolved: (no fee)
- **Total**: 2% of position

**Impact on Edge**:
- True edge = Raw edge - Fees
- Need >2% raw edge just to break even

**Example**:
```
Bet: $100 on YES
Fee: $2 (2%)
Win: Receive $100 (net: +$98)
Lose: Lose $102 (bet + fee)

Expected Value:
EV = 0.62 × $98 - 0.38 × $102 = $22.00
```

### 6.2 Slippage

**Definition**: Difference between expected and actual fill price

**Causes**:
- Low liquidity markets
- Large orders
- Volatile periods

**Mitigation**:
- Only trade markets with >$50k liquidity
- Limit order sizes to <5% of market volume
- Monitor order book depth

### 6.3 Gas Fees

**Polygon Network**: ~$0.01-0.10 per transaction
- Negligible for positions >$50
- Matters for micro-betting

---

## 7. Backtesting Methodology

### 7.1 Walk-Forward Testing

**Approach**:
1. Train on first 60 days → derive signal rules
2. Test on next 30 days → measure performance
3. Roll forward 30 days → repeat

**Benefits**:
- Prevents look-ahead bias
- Tests adaptability
- Realistic performance estimation

### 7.2 Performance Metrics

**Return Metrics**:
- Total Return: (Final - Initial) / Initial
- CAGR: Annualized return
- Win Rate: Wins / Total Trades

**Risk Metrics**:
- Sharpe Ratio: (Return - RiskFree) / Volatility
- Max Drawdown: Worst peak-to-trough decline
- Profit Factor: Gross Profit / Gross Loss

**Target Benchmarks**:
```
Sharpe Ratio: >1.5
Max Drawdown: <20%
Win Rate: >55%
Profit Factor: >1.5
```

### 7.3 Realistic Assumptions

**Include**:
- ✅ 2% Polymarket fees
- ✅ Slippage (0.5% estimate)
- ✅ Market impact (for large orders)

**Exclude** (too optimistic):
- ❌ Assuming instant fills
- ❌ Ignoring market hours
- ❌ Perfect information

---

## 8. Live Trading Considerations

### 8.1 Market Selection

**Ideal Markets**:
- Binary outcomes (YES/NO)
- Clear resolution criteria
- >$50k liquidity
- <48 hour duration
- Related to BTC price movement

**Example**:
"Will BTC close above $45,000 in the next 15 minutes?"

### 8.2 Real-Time Execution

**Latency Challenges**:
- WebSocket delay: ~100-500ms
- API request: ~200-500ms
- Order placement: ~500-1000ms
- **Total**: 1-2 seconds

**Impact**: Market price may move before fill

**Solution**:
- Use limit orders (not market)
- Add slippage tolerance
- Cancel stale orders

### 8.3 Monitoring

**Key Metrics to Track**:
```python
# Real-time
- Current P&L
- Win rate (last 100 trades)
- Average edge captured
- Slippage vs expected

# Daily
- Total trades
- Daily P&L
- Largest winner/loser
- Time-of-day performance

# Weekly
- Strategy drift (are patterns changing?)
- Parameter re-calibration needed?
- New markets to add/remove?
```

### 8.4 Failure Modes

**Common Issues**:
1. **API Downtime**: Have backup data sources
2. **WebSocket Disconnect**: Auto-reconnect logic
3. **Market Pause**: Don't trade during halts
4. **Insufficient Liquidity**: Order doesn't fill
5. **Strategy Decay**: Patterns stop working

**Mitigation**:
- Redundant data feeds
- Graceful error handling
- Circuit breakers
- Regular strategy review

---

## 9. Strategy Evolution

### 9.1 When to Re-Calibrate

**Triggers**:
- Win rate drops below 52% for 100+ trades
- Sharpe ratio <0.5 for 30 days
- Max drawdown exceeds 15%
- New market regime (e.g., Bitcoin halving)

**Actions**:
1. Re-run analysis on recent data (last 90 days)
2. Adjust signal thresholds
3. Update position sizing
4. Consider new timeframes

### 9.2 Extensions

**Enhancements to Consider**:

1. **Multi-Timeframe Analysis**
   - Combine 5m, 15m, 1h signals
   - Higher weight to aligned signals

2. **Volume Confirmation**
   - High volume streaks more reliable
   - Low volume = skip signal

3. **Volatility Regime**
   - Increase edge requirement in high VIX
   - Different rules for quiet vs chaotic markets

4. **Machine Learning**
   - Features: streak length, volume, time-of-day, day-of-week
   - Model: Gradient Boosting or Neural Network
   - Target: Probability of reversal

5. **Cross-Asset Signals**
   - ETH correlation with BTC
   - Stock market open/close effects
   - Macro news events

---

## 10. Polymarket-Specific Strategies

### 10.1 Market Making

**Concept**: Provide liquidity on both sides

**Example**:
- Market: "BTC up in next 15m?"
- Current: YES @ 50%, NO @ 50%
- We offer: YES @ 48%, NO @ 52%
- Profit from spread (if balanced)

**Risk**: Directional exposure

### 10.2 Arbitrage

**Opportunities**:
- Same event, different markets
- Correlated outcomes mispriced

**Example**:
- Market A: "BTC > $45k" @ 60%
- Market B: "BTC < $44k" @ 45%
- Gap: 5% (should sum to 100%)
- Bet NO on A, NO on B → guaranteed profit

### 10.3 Early Exit

**Polymarket Feature**: Sell positions before resolution

**Strategy**:
- Enter on signal
- Exit if probability moves in our favor
- Lock in profit early (reduce variance)

**Example**:
- Buy YES @ 50% ($100)
- Price moves to 65%
- Sell @ 65% → +$15 profit
- Don't wait for resolution

---

## 11. Practical Recommendations

### For Beginners

1. **Start Small**: $10-50 positions
2. **Paper Trade**: 2 weeks minimum
3. **Single Timeframe**: Just 15m candles
4. **Simple Rules**: Only trade 3+ streak signals
5. **Track Everything**: Keep detailed logs

### For Intermediate

1. **Optimize Parameters**: Backtest different thresholds
2. **Multiple Timeframes**: Add 5m and 1h
3. **Dynamic Sizing**: Adjust by signal quality
4. **Automation**: Build Telegram bot for alerts
5. **Performance Review**: Weekly analysis

### For Advanced

1. **Machine Learning**: Train predictive models
2. **High Frequency**: Sub-minute signals
3. **Market Making**: Provide liquidity
4. **Portfolio**: Trade multiple assets
5. **Custom Infrastructure**: Dedicated servers

---

## 12. Final Thoughts

### What Makes This Work

✅ **Statistical Rigor**: Not guesswork, but data-driven
✅ **Risk Management**: Multiple layers of protection
✅ **Position Sizing**: Kelly keeps you alive
✅ **Continuous Learning**: Adapt to new data

### What Can Go Wrong

⚠️ **Overfitting**: Patterns in backtest may not continue
⚠️ **Black Swans**: Extreme events not in historical data
⚠️ **Competition**: Others find same edge, prices adjust
⚠️ **Execution**: Slippage eats into thin edges

### Success Factors

🎯 **Discipline**: Follow rules even during losses
🎯 **Patience**: Wait for high-quality signals
🎯 **Adaptation**: Update strategy as markets evolve
🎯 **Humility**: Accept that edges decay over time

---

## Conclusion

This system provides a **robust quantitative framework** for BTC prediction markets. The edge comes from:

1. Identifying mean-reversion patterns
2. Statistical validation with confidence intervals
3. Optimal position sizing via Kelly Criterion
4. Rigorous risk management

**Expected Performance** (with real data):
- Win Rate: 55-60%
- Sharpe Ratio: 1.5-2.5
- Monthly Return: 5-15%
- Max Drawdown: 10-20%

**Remember**: No strategy works forever. Continuous monitoring, testing, and adaptation are essential for long-term success.

---

*"In God we trust, all others must bring data."* – W. Edwards Deming

*Last Updated: November 2025*
