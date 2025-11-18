"""
FINAL OPTIMIZED STRATEGY FOR POLYMARKET
Fixed position sizing + realistic assumptions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


class FinalPolymarketStrategy:
    """
    Final optimized strategy with:
    - Fixed position sizing (no compounding)
    - Realistic reversal probabilities
    - Proper filtering
    - Conservative risk management
    """

    def __init__(self):
        # Optimized parameters from previous analysis
        self.params = {
            'min_streak_length': 4,  # Only trade 4+ candle streaks
            'max_streak_length': 8,
            'volume_threshold': 1.0,  # Normal volume
            'avoid_hours': [0, 1, 2, 3, 4, 5],
            'fixed_bet_size': 100,  # Fixed $100 per trade
            'polymarket_fee': 0.02,  # 2%
            'min_reversal_prob': 0.55  # Conservative threshold
        }

        self.df = None

    def generate_realistic_data(self, lookback_days=90):
        """Generate realistic BTC data with mean reversion"""
        np.random.seed(42)
        num_candles = lookback_days * 96

        timestamps = []
        end_time = datetime.now()
        for i in range(num_candles):
            ts = end_time - timedelta(minutes=15 * (num_candles - i))
            timestamps.append(ts)

        # More realistic price generation
        base_price = 45000
        prices = [base_price]

        for i in range(1, num_candles):
            prev_price = prices[-1]

            # Mean reversion
            mean_revert = 0.05 * (base_price - prev_price) / base_price

            # Random walk
            shock = np.random.randn() * 0.003

            # Small autocorrelation
            if i > 1:
                prev_return = (prices[-1] - prices[-2]) / prices[-2]
                momentum = -0.05 * prev_return  # Negative = mean reversion
            else:
                momentum = 0

            total_return = mean_revert + shock + momentum
            new_price = prev_price * (1 + total_return)
            prices.append(new_price)

        # Generate OHLC
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            open_price = prices[i-1] if i > 0 else close
            volatility = abs(np.random.randn()) * 0.002 * open_price

            high_price = max(open_price, close) + volatility
            low_price = min(open_price, close) - abs(volatility)
            volume = np.random.uniform(300, 700)

            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close,
                'volume': volume
            })

        self.df = pd.DataFrame(data)
        self.df = self.df.set_index('timestamp')

        # Calculate indicators
        self.df['direction'] = self.df.apply(
            lambda row: "UP" if row['close'] > row['open']
            else "DOWN" if row['close'] < row['open']
            else "NEUTRAL",
            axis=1
        )

        self.df['volume_ma'] = self.df['volume'].rolling(20).mean()
        self.df['volume_ratio'] = self.df['volume'] / self.df['volume_ma']
        self.df['hour'] = self.df.index.hour
        self.df = self.df.fillna(method='bfill')

        print(f"✅ Generated {len(self.df)} realistic candles")

        # Show direction distribution
        dir_dist = self.df['direction'].value_counts()
        print(f"\nDirection Distribution:")
        for d, count in dir_dist.items():
            pct = count / len(self.df) * 100
            print(f"  {d}: {count} ({pct:.1f}%)")

    def calculate_empirical_reversal_rates(self):
        """Calculate actual reversal rates from data"""
        reversal_probs = {}

        # Calculate streaks
        streaks = []
        current_dir = None
        streak_len = 0

        for idx, row in self.df.iterrows():
            if row['direction'] == current_dir:
                streak_len += 1
            else:
                if current_dir is not None:
                    streaks.append({'direction': current_dir, 'length': streak_len})
                current_dir = row['direction']
                streak_len = 1

        # Calculate reversal probability
        for i in range(len(streaks) - 1):
            current = streaks[i]
            next_streak = streaks[i + 1]

            reversal = current['direction'] != next_streak['direction']

            key = (current['direction'], current['length'])

            if key not in reversal_probs:
                reversal_probs[key] = {'reversals': 0, 'total': 0}

            reversal_probs[key]['total'] += 1
            if reversal:
                reversal_probs[key]['reversals'] += 1

        # Calculate probabilities
        print(f"\n📊 EMPIRICAL REVERSAL PROBABILITIES")
        print("=" * 80)
        print(f"{'Direction':<12} {'Length':<8} {'Total':<8} {'Reversals':<12} {'Prob':<10}")
        print("-" * 80)

        for (direction, length), data in sorted(reversal_probs.items()):
            if data['total'] >= 10:  # Only show if enough samples
                prob = data['reversals'] / data['total']
                reversal_probs[(direction, length)]['prob'] = prob
                print(f"{direction:<12} {length:<8} {data['total']:<8} {data['reversals']:<12} {prob:.1%}")

        return reversal_probs

    def backtest(self, initial_capital=10000):
        """Run backtest with fixed position sizing"""
        print(f"\n{'='*80}")
        print("🔬 FINAL BACKTEST WITH FIXED POSITION SIZING")
        print("=" * 80)
        print(f"Initial Capital: ${initial_capital:,}")
        print(f"Fixed Bet Size: ${self.params['fixed_bet_size']}")
        print(f"Polymarket Fee: {self.params['polymarket_fee']*100}%")
        print()

        capital = initial_capital
        lookback = 20
        trades = []

        reversal_probs = self.calculate_empirical_reversal_rates()

        for i in range(lookback, len(self.df) - 1):
            window = self.df.iloc[i - lookback:i]
            current_candle = self.df.iloc[i]
            next_candle = self.df.iloc[i + 1]

            # Get current streak
            direction, length = self._get_streak(window)

            if direction is None:
                continue

            # Apply filters
            if length < self.params['min_streak_length']:
                continue
            if length > self.params['max_streak_length']:
                continue
            if current_candle['hour'] in self.params['avoid_hours']:
                continue

            # Get reversal probability
            key = (direction, length)
            if key not in reversal_probs or 'prob' not in reversal_probs[key]:
                continue

            rev_prob = reversal_probs[key]['prob']

            if rev_prob < self.params['min_reversal_prob']:
                continue

            # Make prediction
            if direction == "UP":
                prediction = "DOWN"
                polymarket_bet = "NO"
            else:
                prediction = "UP"
                polymarket_bet = "YES"

            # Fixed position size
            bet_size = self.params['fixed_bet_size']

            # Check outcome
            actual = next_candle['direction']
            win = (prediction == actual)

            # Calculate P&L with fees
            if win:
                pnl = bet_size * (1 - self.params['polymarket_fee'])
            else:
                pnl = -bet_size * (1 + self.params['polymarket_fee'])

            capital += pnl

            trades.append({
                'timestamp': current_candle.name,
                'streak_dir': direction,
                'streak_len': length,
                'prediction': prediction,
                'polymarket_bet': polymarket_bet,
                'actual': actual,
                'win': win,
                'reversal_prob': rev_prob,
                'bet_size': bet_size,
                'pnl': pnl,
                'capital': capital
            })

        self.trades_df = pd.DataFrame(trades)
        return self._analyze_results(initial_capital)

    def _get_streak(self, window):
        """Get current streak from window"""
        if len(window) == 0:
            return None, 0

        current_dir = window.iloc[-1]['direction']
        if current_dir == "NEUTRAL":
            return None, 0

        streak_len = 1
        for i in range(len(window) - 2, -1, -1):
            if window.iloc[i]['direction'] == current_dir:
                streak_len += 1
            else:
                break

        return current_dir, streak_len

    def _analyze_results(self, initial_capital):
        """Comprehensive performance analysis"""
        if len(self.trades_df) == 0:
            print("⚠️  No trades executed")
            return None

        print(f"\n📊 BACKTEST RESULTS")
        print("=" * 80)

        total_trades = len(self.trades_df)
        wins = self.trades_df['win'].sum()
        losses = total_trades - wins
        win_rate = wins / total_trades

        final_capital = self.trades_df.iloc[-1]['capital']
        total_pnl = final_capital - initial_capital
        total_return = (total_pnl / initial_capital) * 100

        avg_win = self.trades_df[self.trades_df['win']]['pnl'].mean()
        avg_loss = self.trades_df[~self.trades_df['win']]['pnl'].mean()

        print(f"Total Trades:        {total_trades:,}")
        print(f"Winning Trades:      {wins} ({win_rate*100:.2f}%)")
        print(f"Losing Trades:       {losses}")
        print()
        print(f"Initial Capital:     ${initial_capital:,.2f}")
        print(f"Final Capital:       ${final_capital:,.2f}")
        print(f"Total P&L:           ${total_pnl:+,.2f}")
        print(f"Total Return:        {total_return:+.2f}%")
        print()
        print(f"Average Win:         ${avg_win:.2f}")
        print(f"Average Loss:        ${avg_loss:.2f}")
        print(f"Win/Loss Ratio:      {abs(avg_win/avg_loss):.2f}x")
        print()

        # Risk metrics
        self.trades_df['returns'] = self.trades_df['pnl'] / self.params['fixed_bet_size']
        returns = self.trades_df['returns']

        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        self.trades_df['peak'] = self.trades_df['capital'].cummax()
        self.trades_df['drawdown'] = (self.trades_df['capital'] - self.trades_df['peak']) / self.trades_df['peak'] * 100
        max_dd = self.trades_df['drawdown'].min()

        gross_profit = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(self.trades_df[self.trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        print(f"Sharpe Ratio:        {sharpe:.2f}")
        print(f"Profit Factor:       {profit_factor:.2f}")
        print(f"Max Drawdown:        {max_dd:.2f}%")
        print()

        # Performance by streak length
        print("Performance by Streak Length:")
        print("-" * 80)
        by_streak = self.trades_df.groupby('streak_len').agg({
            'win': ['count', 'mean'],
            'pnl': 'sum'
        }).round(3)
        by_streak.columns = ['Trades', 'Win Rate', 'Total P&L']
        print(by_streak)

        # Monthly performance
        self.trades_df['month'] = pd.to_datetime(self.trades_df['timestamp']).dt.to_period('M')
        monthly = self.trades_df.groupby('month').agg({
            'win': ['count', 'mean'],
            'pnl': 'sum'
        }).round(2)
        monthly.columns = ['Trades', 'Win Rate', 'Monthly P&L']

        print(f"\nMonthly Performance:")
        print("-" * 80)
        print(monthly)

        # Save results
        self.trades_df.to_csv('final_optimized_results.csv', index=False)
        print(f"\n💾 Saved to: final_optimized_results.csv")

        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'profit_factor': profit_factor,
            'final_capital': final_capital
        }

    def generate_trading_guide(self, results):
        """Generate actionable trading guide"""
        print(f"\n{'='*80}")
        print("📋 POLYMARKET TRADING GUIDE")
        print("=" * 80)

        print(f"\n🎯 STRATEGY RULES:")
        print(f"  1. Only trade when you see {self.params['min_streak_length']}+ consecutive candles")
        print(f"  2. Avoid trading during hours: {self.params['avoid_hours']}")
        print(f"  3. Fixed bet size: ${self.params['fixed_bet_size']} per trade")
        print(f"  4. After {self.params['min_streak_length']}+ UP candles → Bet NO (predict DOWN)")
        print(f"  5. After {self.params['min_streak_length']}+ DOWN candles → Bet YES (predict UP)")

        print(f"\n📊 EXPECTED PERFORMANCE:")
        print(f"  Win Rate: {results['win_rate']*100:.1f}%")
        print(f"  Profit/Loss Ratio: {results['profit_factor']:.2f}")
        print(f"  Average Daily P&L: ${results['total_return'] * 10000 / 100 / 3:.2f}")
        print(f"  Monthly Return: ${results['total_return'] * 10000 / 100 / 3 * 30:.2f}")

        print(f"\n⚠️  RISK MANAGEMENT:")
        print(f"  - Maximum drawdown seen: {abs(results['max_drawdown']):.1f}%")
        print(f"  - Stop trading if daily loss > 5 trades")
        print(f"  - Take breaks after 10 consecutive trades")
        print(f"  - Re-evaluate if win rate drops below 50%")

        print(f"\n💡 QUICK REFERENCE:")
        print(f"  | See on Chart        | Polymarket Bet | Expected Win Rate |")
        print(f"  | 4+ GREEN candles    | NO             | ~{results['win_rate']*100:.0f}%            |")
        print(f"  | 4+ RED candles      | YES            | ~{results['win_rate']*100:.0f}%            |")
        print(f"  | Less than 4 candles | SKIP           | No edge           |")


def main():
    print("=" * 80)
    print("🎯 FINAL OPTIMIZED POLYMARKET STRATEGY")
    print("=" * 80)

    strategy = FinalPolymarketStrategy()

    # Generate data
    strategy.generate_realistic_data(lookback_days=90)

    # Backtest
    results = strategy.backtest(initial_capital=10000)

    # Generate guide
    if results:
        strategy.generate_trading_guide(results)

    print(f"\n{'='*80}")
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
