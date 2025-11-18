"""
Backtesting Framework for BTC Streak Trading Strategy
Tests historical performance of reversal/continuation signals
"""

import pandas as pd
import numpy as np
from datetime import datetime
from btc_streak_analysis import BTCStreakAnalyzer


class StreakBacktester:
    """Backtest streak-based trading strategies with realistic transaction costs"""

    def __init__(self, analyzer: BTCStreakAnalyzer, signals: list):
        self.analyzer = analyzer
        self.signals = signals
        self.df = analyzer.df.copy()
        self.trades = []
        self.equity_curve = []

    def calculate_current_streak(self, window_data):
        """Calculate the current streak from a window of candles"""
        if len(window_data) == 0:
            return None, 0

        current_direction = window_data.iloc[-1]["direction"]
        streak_length = 1

        # Count backwards to find streak length
        for i in range(len(window_data) - 2, -1, -1):
            if window_data.iloc[i]["direction"] == current_direction:
                streak_length += 1
            else:
                break

        return current_direction, streak_length

    def find_matching_signal(self, direction, streak_length):
        """Find if current streak matches any of our trading signals"""
        for signal in self.signals:
            # Parse the condition to extract direction and streak length
            condition = signal["condition"]

            if f"{streak_length} consecutive {direction}" in condition:
                return signal

        return None

    def run_backtest(self, initial_capital=10000, bet_size_pct=0.02, polymarket_fee=0.02):
        """
        Run backtest simulation

        Args:
            initial_capital: Starting capital ($)
            bet_size_pct: Percentage of capital to bet per trade (2% default)
            polymarket_fee: Polymarket trading fee (2% default)
        """
        print("=" * 80)
        print("🔬 RUNNING BACKTEST SIMULATION")
        print("=" * 80)
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print(f"Bet Size: {bet_size_pct * 100}% of capital")
        print(f"Polymarket Fee: {polymarket_fee * 100}%")
        print(f"Lookback Window: 20 candles")
        print()

        capital = initial_capital
        lookback = 20  # Number of candles to look back for streak detection

        for i in range(lookback, len(self.df)):
            timestamp = self.df.index[i]
            current_candle = self.df.iloc[i]

            # Get lookback window
            window = self.df.iloc[i - lookback:i]

            # Calculate current streak
            direction, streak_length = self.calculate_current_streak(window)

            # Check if we have a signal for this streak
            signal = self.find_matching_signal(direction, streak_length)

            if signal:
                # Determine bet
                prediction = signal["prediction"]
                probability = signal["probability"]
                edge = signal["edge"]

                # Calculate bet size using Kelly Criterion (fractional)
                # Kelly = (p * (b + 1) - 1) / b, where b = odds - 1
                # For binary bet: Kelly = p - (1-p) = 2p - 1
                kelly_fraction = 2 * probability - 1
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%

                # Use conservative bet sizing (fraction of Kelly)
                bet_amount = capital * bet_size_pct * kelly_fraction

                if bet_amount < 1:  # Skip if bet too small
                    continue

                # Determine actual outcome (next candle direction)
                if i + 1 < len(self.df):
                    next_candle = self.df.iloc[i + 1]
                    actual_direction = next_candle["direction"]

                    # Check if prediction was correct
                    win = (prediction == actual_direction)

                    # Calculate P&L
                    # On Polymarket, you buy YES or NO shares
                    # If correct: gain = bet_amount * (1 - fee)
                    # If wrong: loss = -bet_amount * (1 + fee)
                    if win:
                        pnl = bet_amount * (1 - polymarket_fee)
                    else:
                        pnl = -bet_amount * (1 + polymarket_fee)

                    capital += pnl

                    # Record trade
                    self.trades.append({
                        "timestamp": timestamp,
                        "streak_direction": direction,
                        "streak_length": streak_length,
                        "prediction": prediction,
                        "actual": actual_direction,
                        "win": win,
                        "bet_amount": bet_amount,
                        "pnl": pnl,
                        "capital": capital,
                        "edge": edge,
                        "probability": probability
                    })

            # Record equity curve
            self.equity_curve.append({
                "timestamp": timestamp,
                "capital": capital
            })

        self.trades_df = pd.DataFrame(self.trades)
        self.equity_df = pd.DataFrame(self.equity_curve)

        return self.analyze_performance(initial_capital)

    def analyze_performance(self, initial_capital):
        """Calculate comprehensive performance metrics"""
        if len(self.trades_df) == 0:
            print("⚠️  No trades executed in backtest period")
            return None

        print(f"📊 BACKTEST RESULTS")
        print("=" * 80)

        # Basic stats
        total_trades = len(self.trades_df)
        winning_trades = len(self.trades_df[self.trades_df["win"] == True])
        losing_trades = len(self.trades_df[self.trades_df["win"] == False])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # P&L stats
        total_pnl = self.trades_df["pnl"].sum()
        avg_win = self.trades_df[self.trades_df["win"] == True]["pnl"].mean() if winning_trades > 0 else 0
        avg_loss = self.trades_df[self.trades_df["win"] == False]["pnl"].mean() if losing_trades > 0 else 0

        # Returns
        final_capital = self.equity_df.iloc[-1]["capital"]
        total_return = ((final_capital - initial_capital) / initial_capital) * 100

        # Risk metrics
        returns = self.equity_df["capital"].pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(96 * 365) if len(returns) > 0 and returns.std() > 0 else 0

        # Max drawdown
        equity_curve = self.equity_df["capital"]
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        # Profit factor
        gross_profit = self.trades_df[self.trades_df["pnl"] > 0]["pnl"].sum()
        gross_loss = abs(self.trades_df[self.trades_df["pnl"] < 0]["pnl"].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        print(f"Total Trades:        {total_trades}")
        print(f"Winning Trades:      {winning_trades} ({win_rate * 100:.2f}%)")
        print(f"Losing Trades:       {losing_trades}")
        print()
        print(f"Initial Capital:     ${initial_capital:,.2f}")
        print(f"Final Capital:       ${final_capital:,.2f}")
        print(f"Total P&L:           ${total_pnl:,.2f}")
        print(f"Total Return:        {total_return:.2f}%")
        print()
        print(f"Average Win:         ${avg_win:.2f}")
        print(f"Average Loss:        ${avg_loss:.2f}")
        print(f"Profit Factor:       {profit_factor:.2f}")
        print()
        print(f"Sharpe Ratio:        {sharpe_ratio:.2f}")
        print(f"Max Drawdown:        {max_drawdown:.2f}%")
        print()

        # Trade distribution by streak length
        print("📈 Performance by Streak Length:")
        streak_perf = self.trades_df.groupby("streak_length").agg({
            "win": ["count", "sum", "mean"],
            "pnl": "sum"
        }).round(2)
        print(streak_perf)
        print()

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "profit_factor": profit_factor,
            "final_capital": final_capital
        }

    def save_results(self, filename="backtest_results.csv"):
        """Save trade log to CSV"""
        if self.trades_df is not None and len(self.trades_df) > 0:
            self.trades_df.to_csv(filename, index=False)
            print(f"💾 Trade log saved to {filename}")


def main():
    """Run backtest on BTC streak strategy"""
    print("=" * 80)
    print("🚀 BTC STREAK STRATEGY BACKTESTER")
    print("=" * 80)
    print()

    # Initialize analyzer
    analyzer = BTCStreakAnalyzer(interval='15m', lookback_days=90)

    if not analyzer.fetch_data():
        return

    analyzer.calculate_direction()
    streak_df = analyzer.analyze_streaks()
    reversal_stats = analyzer.calculate_reversal_probability(streak_df)
    ci_df = analyzer.calculate_confidence_intervals(reversal_stats)

    # Generate signals with stricter criteria for backtesting
    signals = analyzer.generate_trading_signals(ci_df, min_edge=0.15, min_confidence=0.60)

    if not signals:
        print("⚠️  No signals generated - try relaxing criteria")
        return

    # Run backtest
    backtester = StreakBacktester(analyzer, signals)
    results = backtester.run_backtest(
        initial_capital=10000,
        bet_size_pct=0.02,  # 2% of capital per trade
        polymarket_fee=0.02  # 2% Polymarket fee
    )

    if results:
        backtester.save_results()

        print()
        print("=" * 80)
        print("💡 INTERPRETATION & RECOMMENDATIONS")
        print("=" * 80)
        print("""
        ✅ Key Takeaways:

        1. Win Rate: A good streak strategy should have 55%+ win rate
        2. Sharpe Ratio: Above 1.0 is decent, above 2.0 is excellent
        3. Max Drawdown: Keep below 20% for sustainable trading
        4. Profit Factor: Above 1.5 indicates positive expectancy

        ⚠️  Important Considerations:

        - This backtest uses synthetic data (Binance API was blocked)
        - Real market data may show different patterns
        - Polymarket liquidity varies - may not always get filled
        - Market conditions change - strategies degrade over time

        🎯 Next Steps for Live Trading:

        1. Test on REAL historical data from Binance/other sources
        2. Implement real-time WebSocket monitoring
        3. Add position sizing optimization
        4. Build Polymarket API integration
        5. Start with paper trading to validate
        6. Monitor performance and adjust parameters
        """)


if __name__ == "__main__":
    main()
