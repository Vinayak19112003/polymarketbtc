"""
IMPROVED BTC STREAK STRATEGY
Fixes all identified loopholes and optimizes for real market conditions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json


class ImprovedBTCStrategy:
    """
    Enhanced strategy with realistic market assumptions

    Key Improvements:
    1. Realistic reversal probabilities (not 100%)
    2. Volume filtering
    3. Volatility adjustment
    4. Time-of-day filtering
    5. Dynamic position sizing
    6. Multiple parameter optimization
    """

    def __init__(self, lookback_days=90):
        self.lookback_days = lookback_days
        self.df = None

        # Optimized parameters (will be tuned)
        self.params = {
            'min_streak_length': 3,
            'max_streak_length': 8,
            'min_reversal_prob': 0.55,
            'min_sample_size': 20,
            'volume_threshold': 1.2,  # 120% of average volume
            'volatility_threshold': 2.0,  # Max 2x average volatility
            'avoid_hours': [0, 1, 2, 3, 4, 5],  # Low liquidity hours
            'kelly_fraction': 0.25,
            'max_position_pct': 0.05  # 5% of capital
        }

    def generate_realistic_data(self):
        """Generate realistic BTC price data with proper statistical properties"""
        np.random.seed(42)

        num_candles = self.lookback_days * 96  # 96 15-min candles per day

        timestamps = []
        end_time = datetime.now()
        for i in range(num_candles):
            ts = end_time - timedelta(minutes=15 * (num_candles - i))
            timestamps.append(ts)

        # Generate realistic price movement
        base_price = 45000
        prices = [base_price]

        # Realistic parameters
        trend_strength = 0.0002  # Small drift
        mean_reversion_speed = 0.15
        volatility = 0.003  # 0.3% per 15min

        for i in range(1, num_candles):
            # Mean-reverting with trend
            prev_price = prices[-1]

            # Mean reversion to base price
            mean_revert = mean_reversion_speed * (base_price - prev_price) / base_price

            # Random shock
            shock = np.random.randn() * volatility

            # Small trend
            trend = trend_strength

            # Momentum (autocorrelation)
            if i > 1:
                prev_return = (prices[-1] - prices[-2]) / prices[-2]
                momentum = 0.1 * prev_return  # Some momentum
            else:
                momentum = 0

            # Combine effects
            total_return = mean_revert + shock + trend + momentum
            new_price = prev_price * (1 + total_return)

            prices.append(new_price)

        # Generate OHLC from prices
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            open_price = prices[i-1] if i > 0 else close

            # High/Low based on volatility
            candle_volatility = abs(np.random.randn()) * volatility * open_price * 0.5
            high_price = max(open_price, close) + candle_volatility
            low_price = min(open_price, close) - candle_volatility

            # Volume with realistic variation
            base_volume = 500
            volume = base_volume * (1 + np.random.randn() * 0.3)
            volume = max(volume, 100)

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

        print(f"✅ Generated {len(self.df)} realistic candles")

    def calculate_indicators(self):
        """Calculate technical indicators and features"""
        # Direction
        self.df['direction'] = self.df.apply(
            lambda row: "UP" if row['close'] > row['open']
            else "DOWN" if row['close'] < row['open']
            else "NEUTRAL",
            axis=1
        )

        # Price change
        self.df['pct_change'] = ((self.df['close'] - self.df['open']) / self.df['open']) * 100

        # Volume indicators
        self.df['volume_ma'] = self.df['volume'].rolling(20).mean()
        self.df['volume_ratio'] = self.df['volume'] / self.df['volume_ma']

        # Volatility
        self.df['returns'] = self.df['close'].pct_change()
        self.df['volatility'] = self.df['returns'].rolling(20).std()
        self.df['avg_volatility'] = self.df['volatility'].rolling(50).mean()
        self.df['volatility_ratio'] = self.df['volatility'] / self.df['avg_volatility']

        # Hour of day
        self.df['hour'] = self.df.index.hour

        # Fill NaN values
        self.df = self.df.fillna(method='bfill')

    def calculate_streaks_with_context(self):
        """Calculate streaks with additional context"""
        streaks = []
        current_direction = None
        streak_length = 0
        streak_volumes = []
        streak_volatilities = []

        for idx, row in self.df.iterrows():
            if row['direction'] == current_direction:
                streak_length += 1
                streak_volumes.append(row['volume_ratio'])
                streak_volatilities.append(row['volatility_ratio'])
            else:
                if current_direction is not None:
                    streaks.append({
                        'direction': current_direction,
                        'length': streak_length,
                        'avg_volume_ratio': np.mean(streak_volumes) if streak_volumes else 1,
                        'avg_volatility_ratio': np.mean(streak_volatilities) if streak_volatilities else 1,
                        'hour': row['hour']
                    })

                current_direction = row['direction']
                streak_length = 1
                streak_volumes = [row['volume_ratio']]
                streak_volatilities = [row['volatility_ratio']]

        return pd.DataFrame(streaks)

    def analyze_reversal_probabilities(self):
        """Analyze reversal probabilities with realistic expectations"""
        print("\n" + "="*80)
        print("📊 ANALYZING REVERSAL PROBABILITIES (REALISTIC)")
        print("="*80)

        streak_df = self.calculate_streaks_with_context()

        reversal_data = []

        for i in range(len(streak_df) - 1):
            current = streak_df.iloc[i]
            next_streak = streak_df.iloc[i + 1]

            reversal = current['direction'] != next_streak['direction']

            reversal_data.append({
                'direction': current['direction'],
                'length': current['length'],
                'reversal': reversal,
                'volume_ratio': current['avg_volume_ratio'],
                'volatility_ratio': current['avg_volatility_ratio'],
                'hour': current['hour']
            })

        reversal_df = pd.DataFrame(reversal_data)

        # Calculate reversal probability by streak length
        results = {}

        for direction in ['UP', 'DOWN']:
            for length in range(1, 10):
                mask = (reversal_df['direction'] == direction) & (reversal_df['length'] == length)
                subset = reversal_df[mask]

                if len(subset) >= 5:
                    reversal_prob = subset['reversal'].mean()

                    # Apply filters for high-quality signals
                    high_volume = subset[subset['volume_ratio'] >= self.params['volume_threshold']]
                    low_volatility = subset[subset['volatility_ratio'] <= self.params['volatility_threshold']]

                    filtered_reversal_prob = high_volume['reversal'].mean() if len(high_volume) >= 5 else reversal_prob

                    results[(direction, length)] = {
                        'total_count': len(subset),
                        'base_reversal_prob': reversal_prob,
                        'filtered_reversal_prob': filtered_reversal_prob,
                        'filtered_count': len(high_volume)
                    }

        # Print results
        print(f"\nReversal Probabilities by Streak Length:")
        print("-" * 80)
        print(f"{'Direction':<10} {'Length':<8} {'Total':<8} {'Base Prob':<12} {'Filtered Prob':<15} {'Filtered N':<12}")
        print("-" * 80)

        for (direction, length), data in sorted(results.items()):
            print(f"{direction:<10} {length:<8} {data['total_count']:<8} "
                  f"{data['base_reversal_prob']:.1%}{'':>7} {data['filtered_reversal_prob']:.1%}{'':>10} "
                  f"{data['filtered_count']:<12}")

        return results

    def optimize_parameters(self):
        """Find optimal parameters through grid search"""
        print("\n" + "="*80)
        print("🔍 OPTIMIZING STRATEGY PARAMETERS")
        print("="*80)

        best_sharpe = -999
        best_params = None

        # Parameter grid
        min_streak_options = [2, 3, 4]
        min_prob_options = [0.52, 0.55, 0.58]
        volume_threshold_options = [1.0, 1.2, 1.5]

        results_log = []

        for min_streak in min_streak_options:
            for min_prob in min_prob_options:
                for vol_threshold in volume_threshold_options:
                    # Test this combination
                    test_params = self.params.copy()
                    test_params['min_streak_length'] = min_streak
                    test_params['min_reversal_prob'] = min_prob
                    test_params['volume_threshold'] = vol_threshold

                    # Run backtest
                    sharpe, total_return, win_rate, trades = self._quick_backtest(test_params)

                    results_log.append({
                        'min_streak': min_streak,
                        'min_prob': min_prob,
                        'vol_threshold': vol_threshold,
                        'sharpe': sharpe,
                        'return': total_return,
                        'win_rate': win_rate,
                        'trades': trades
                    })

                    if sharpe > best_sharpe and trades >= 100:
                        best_sharpe = sharpe
                        best_params = test_params.copy()

        # Show top 5 combinations
        results_df = pd.DataFrame(results_log)
        results_df = results_df.sort_values('sharpe', ascending=False)

        print("\n📈 Top 5 Parameter Combinations:")
        print(results_df.head(10).to_string(index=False))

        if best_params:
            self.params = best_params
            print(f"\n✅ Best Parameters Selected:")
            print(json.dumps(best_params, indent=2))

        return best_params

    def _quick_backtest(self, params):
        """Quick backtest for optimization"""
        capital = 10000
        lookback = 20

        wins = 0
        losses = 0
        equity_curve = [capital]

        for i in range(lookback, len(self.df) - 1):
            window = self.df.iloc[i - lookback:i]

            # Calculate current streak
            direction, length = self._get_current_streak(window)

            if direction is None or length < params['min_streak_length']:
                continue

            # Check filters
            current_candle = self.df.iloc[i]
            if current_candle['volume_ratio'] < params['volume_threshold']:
                continue
            if current_candle['hour'] in params['avoid_hours']:
                continue

            # Simple reversal prediction
            # In real backtest we'd use historical probabilities
            # For optimization, use simplified logic
            next_candle = self.df.iloc[i + 1]
            next_direction = next_candle['direction']

            # Predict reversal
            if direction == "UP":
                predicted = "DOWN"
            else:
                predicted = "UP"

            # Check if correct
            win = (predicted == next_direction)

            # Position size
            bet_size = capital * params['max_position_pct']

            # P&L
            if win:
                pnl = bet_size * 0.98  # -2% fee
                wins += 1
            else:
                pnl = -bet_size * 1.02
                losses += 1

            capital += pnl
            equity_curve.append(capital)

        # Calculate metrics
        total_trades = wins + losses
        if total_trades == 0:
            return -999, 0, 0, 0

        win_rate = wins / total_trades
        total_return = ((capital - 10000) / 10000) * 100

        # Sharpe
        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(96 * 252) if returns.std() > 0 else 0
        else:
            sharpe = 0

        return sharpe, total_return, win_rate, total_trades

    def _get_current_streak(self, window):
        """Get current streak from window"""
        if len(window) == 0:
            return None, 0

        current_direction = window.iloc[-1]['direction']
        if current_direction == "NEUTRAL":
            return None, 0

        streak_length = 1
        for i in range(len(window) - 2, -1, -1):
            if window.iloc[i]['direction'] == current_direction:
                streak_length += 1
            else:
                break

        return current_direction, streak_length

    def run_full_backtest(self, initial_capital=10000):
        """Run complete backtest with optimized parameters"""
        print("\n" + "="*80)
        print("🔬 RUNNING FULL BACKTEST WITH OPTIMIZED PARAMETERS")
        print("="*80)

        capital = initial_capital
        lookback = 20

        trades = []

        # Get reversal probabilities
        reversal_probs = self.analyze_reversal_probabilities()

        for i in range(lookback, len(self.df) - 1):
            window = self.df.iloc[i - lookback:i]
            current_candle = self.df.iloc[i]
            next_candle = self.df.iloc[i + 1]

            # Get current streak
            direction, length = self._get_current_streak(window)

            if direction is None:
                continue

            # Apply filters
            if length < self.params['min_streak_length']:
                continue
            if length > self.params['max_streak_length']:
                continue
            if current_candle['volume_ratio'] < self.params['volume_threshold']:
                continue
            if current_candle['volatility_ratio'] > self.params['volatility_threshold']:
                continue
            if current_candle['hour'] in self.params['avoid_hours']:
                continue

            # Get reversal probability
            key = (direction, length)
            if key not in reversal_probs:
                continue

            prob_data = reversal_probs[key]
            reversal_prob = prob_data['filtered_reversal_prob']

            if reversal_prob < self.params['min_reversal_prob']:
                continue

            # Make prediction
            if direction == "UP":
                prediction = "DOWN"
                polymarket_bet = "NO"
            else:
                prediction = "UP"
                polymarket_bet = "YES"

            # Calculate position size (Kelly Criterion)
            edge = reversal_prob - 0.50
            kelly = edge / 0.50 if edge > 0 else 0
            position_size = capital * kelly * self.params['kelly_fraction']
            position_size = min(position_size, capital * self.params['max_position_pct'])
            position_size = max(position_size, 0)

            if position_size < 10:
                continue

            # Check outcome
            actual = next_candle['direction']
            win = (prediction == actual)

            # Calculate P&L
            if win:
                pnl = position_size * 0.98  # -2% fee
            else:
                pnl = -position_size * 1.02  # -2% fee

            capital += pnl

            trades.append({
                'timestamp': current_candle.name,
                'streak_direction': direction,
                'streak_length': length,
                'prediction': prediction,
                'polymarket_bet': polymarket_bet,
                'actual': actual,
                'win': win,
                'reversal_prob': reversal_prob,
                'edge': edge,
                'position_size': position_size,
                'pnl': pnl,
                'capital': capital,
                'volume_ratio': current_candle['volume_ratio'],
                'volatility_ratio': current_candle['volatility_ratio']
            })

        self.trades_df = pd.DataFrame(trades)

        return self._analyze_performance(initial_capital)

    def _analyze_performance(self, initial_capital):
        """Analyze backtest performance"""
        if len(self.trades_df) == 0:
            print("⚠️  No trades executed")
            return None

        print(f"\n📊 BACKTEST PERFORMANCE REPORT")
        print("=" * 80)

        total_trades = len(self.trades_df)
        wins = self.trades_df['win'].sum()
        losses = total_trades - wins
        win_rate = wins / total_trades

        final_capital = self.trades_df.iloc[-1]['capital']
        total_return = ((final_capital - initial_capital) / initial_capital) * 100

        avg_win = self.trades_df[self.trades_df['win'] == True]['pnl'].mean()
        avg_loss = self.trades_df[self.trades_df['win'] == False]['pnl'].mean()

        # Sharpe
        self.trades_df['returns'] = self.trades_df['capital'].pct_change()
        returns = self.trades_df['returns'].dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        # Max drawdown
        self.trades_df['peak'] = self.trades_df['capital'].cummax()
        self.trades_df['drawdown'] = (self.trades_df['capital'] - self.trades_df['peak']) / self.trades_df['peak'] * 100
        max_drawdown = self.trades_df['drawdown'].min()

        # Profit factor
        gross_profit = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(self.trades_df[self.trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        print(f"Total Trades:        {total_trades:,}")
        print(f"Winning Trades:      {wins} ({win_rate*100:.2f}%)")
        print(f"Losing Trades:       {losses}")
        print()
        print(f"Initial Capital:     ${initial_capital:,.2f}")
        print(f"Final Capital:       ${final_capital:,.2f}")
        print(f"Total P&L:           ${final_capital - initial_capital:+,.2f}")
        print(f"Total Return:        {total_return:+.2f}%")
        print()
        print(f"Average Win:         ${avg_win:.2f}")
        print(f"Average Loss:        ${avg_loss:.2f}")
        print(f"Win/Loss Ratio:      {abs(avg_win/avg_loss):.2f}x")
        print()
        print(f"Sharpe Ratio:        {sharpe:.2f}")
        print(f"Profit Factor:       {profit_factor:.2f}")
        print(f"Max Drawdown:        {max_drawdown:.2f}%")
        print()

        # Performance by streak length
        print("Performance by Streak Length:")
        print("-" * 80)
        perf_by_streak = self.trades_df.groupby('streak_length').agg({
            'win': ['count', 'mean'],
            'pnl': 'sum',
            'edge': 'mean'
        }).round(3)
        print(perf_by_streak)

        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'final_capital': final_capital
        }

    def save_results(self):
        """Save detailed results"""
        if self.trades_df is not None and len(self.trades_df) > 0:
            self.trades_df.to_csv('improved_backtest_results.csv', index=False)
            print(f"\n💾 Results saved to: improved_backtest_results.csv")

        # Save parameters
        with open('optimized_parameters.json', 'w') as f:
            json.dump(self.params, f, indent=2)
        print(f"💾 Parameters saved to: optimized_parameters.json")


def main():
    """Run improved strategy analysis and backtest"""
    print("=" * 80)
    print("🚀 IMPROVED BTC STREAK STRATEGY - FULL ANALYSIS")
    print("=" * 80)

    strategy = ImprovedBTCStrategy(lookback_days=90)

    # Generate realistic data
    strategy.generate_realistic_data()

    # Calculate indicators
    strategy.calculate_indicators()

    # Analyze reversal probabilities
    strategy.analyze_reversal_probabilities()

    # Optimize parameters
    strategy.optimize_parameters()

    # Run full backtest
    results = strategy.run_full_backtest(initial_capital=10000)

    # Save results
    strategy.save_results()

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)

    if results:
        print(f"\n🎯 FINAL RESULTS SUMMARY:")
        print(f"   Win Rate: {results['win_rate']*100:.2f}%")
        print(f"   Total Return: {results['total_return']:+.2f}%")
        print(f"   Sharpe Ratio: {results['sharpe']:.2f}")
        print(f"   Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"   Profit Factor: {results['profit_factor']:.2f}")


if __name__ == "__main__":
    main()
