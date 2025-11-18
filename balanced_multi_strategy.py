"""
BALANCED MULTI-STRATEGY FOR POLYMARKET
Goal: 10+ trades/day while maintaining >52% win rate
Quality over quantity
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


class BalancedMultiStrategy:
    """
    Balanced approach:
    1. Streak Reversal (4+ candles only - high quality)
    2. Strong RSI Extremes (>75 or <25 - very strong)
    3. Volume + Direction confluence
    4. Extended streaks (5+ candles - premium setup)

    Target: 10-12 trades/day with >52% win rate
    """

    def __init__(self):
        self.params = {
            # Strategy 1: Regular Streaks (4+ candles)
            'min_streak': 4,
            'max_streak': 8,

            # Strategy 2: Extended Streaks (5+ with higher confidence)
            'extended_streak': 5,
            'extended_prob': 0.54,

            # Strategy 3: Very Strong RSI
            'rsi_period': 14,
            'rsi_very_overbought': 75,  # More extreme
            'rsi_very_oversold': 25,     # More extreme

            # Strategy 4: Volume Confirmation
            'volume_streak_threshold': 1.5,  # Volume + Streak

            # Global
            'fixed_bet_size': 100,
            'polymarket_fee': 0.02,
            'avoid_hours': [0, 1, 2, 3, 4, 5],
            'max_trades_per_day': 15
        }
        self.df = None

    def generate_2year_data(self):
        """Generate 2 years of data"""
        np.random.seed(42)
        num_candles = 730 * 96

        print(f"📊 Generating 2-year data ({num_candles:,} candles)...")

        timestamps = []
        end_time = datetime.now()
        for i in range(num_candles):
            ts = end_time - timedelta(minutes=15 * (num_candles - i))
            timestamps.append(ts)

        # Price generation
        base_price = 40000
        prices = [base_price]

        for i in range(1, num_candles):
            prev_price = prices[-1]

            cycle_pos = (i % 10000) / 10000
            if cycle_pos < 0.3:
                trend = 0.0003
            elif cycle_pos < 0.6:
                trend = -0.0003
            else:
                trend = 0

            mean_revert = 0.025 * (base_price - prev_price) / base_price
            shock = np.random.randn() * 0.004

            if i > 1:
                prev_return = (prices[-1] - prices[-2]) / prices[-2]
                momentum = -0.025 * prev_return
            else:
                momentum = 0

            total_return = mean_revert + shock + momentum + trend
            new_price = prev_price * (1 + total_return)
            prices.append(new_price)

        # OHLC generation
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            open_price = prices[i-1] if i > 0 else close
            base_vol = abs(np.random.randn()) * 0.002 * open_price

            if np.random.random() < 0.1:
                volume = np.random.uniform(850, 1500)
                volatility = base_vol * 1.5
            else:
                volume = np.random.uniform(400, 700)
                volatility = base_vol

            high_price = max(open_price, close) + volatility
            low_price = min(open_price, close) - abs(volatility)

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
        self._calculate_indicators()

        print(f"✅ Generated {len(self.df):,} candles")

    def _calculate_indicators(self):
        """Calculate indicators"""
        # Direction
        self.df['direction'] = self.df.apply(
            lambda row: "UP" if row['close'] > row['open']
            else "DOWN" if row['close'] < row['open']
            else "NEUTRAL",
            axis=1
        )

        # Volume
        self.df['volume_ma'] = self.df['volume'].rolling(20).mean()
        self.df['volume_ratio'] = self.df['volume'] / self.df['volume_ma']

        # RSI
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))

        # Time
        self.df['hour'] = self.df.index.hour

        self.df = self.df.bfill()

    def backtest(self, initial_capital=10000):
        """Backtest balanced strategy"""
        print(f"\n{'='*80}")
        print("🔬 BALANCED MULTI-STRATEGY BACKTEST")
        print("="*80)
        print("Goal: 10+ trades/day with >52% win rate\n")

        capital = initial_capital
        lookback = 30
        trades = []
        daily_trades = {}

        print("⏳ Processing...")
        progress_interval = len(self.df) // 10

        for i in range(lookback, len(self.df) - 1):
            if i % progress_interval == 0:
                print(f"Progress: {(i/len(self.df)*100):.0f}%")

            current_date = self.df.index[i].date()
            current_candle = self.df.iloc[i]
            next_candle = self.df.iloc[i + 1]

            # Daily limit
            if current_date not in daily_trades:
                daily_trades[current_date] = 0

            if daily_trades[current_date] >= self.params['max_trades_per_day']:
                continue

            if current_candle['hour'] in self.params['avoid_hours']:
                continue

            # Get streak info
            window = self.df.iloc[i - lookback:i]
            direction, length = self._get_streak(window)

            if direction is None or direction == "NEUTRAL":
                continue

            # Check all signal types
            signal = None

            # SIGNAL TYPE 1: Extended Streak (5+ candles) - Premium
            if length >= self.params['extended_streak']:
                signal = {
                    'type': 'EXTENDED_STREAK',
                    'detail': f'{length} {direction}',
                    'prediction': 'DOWN' if direction == 'UP' else 'UP',
                    'bet': 'NO' if direction == 'UP' else 'YES',
                    'confidence': min(0.54 + (length - 5) * 0.01, 0.59)
                }

            # SIGNAL TYPE 2: Regular Streak (4 candles) + Volume Confirmation
            elif length == 4:
                if current_candle['volume_ratio'] >= self.params['volume_streak_threshold']:
                    signal = {
                        'type': 'STREAK_VOLUME',
                        'detail': f'4 {direction} + Vol {current_candle["volume_ratio"]:.1f}x',
                        'prediction': 'DOWN' if direction == 'UP' else 'UP',
                        'bet': 'NO' if direction == 'UP' else 'YES',
                        'confidence': 0.54
                    }
                else:
                    # Regular 4-candle without volume
                    signal = {
                        'type': 'STREAK_REGULAR',
                        'detail': f'4 {direction}',
                        'prediction': 'DOWN' if direction == 'UP' else 'UP',
                        'bet': 'NO' if direction == 'UP' else 'YES',
                        'confidence': 0.53
                    }

            # SIGNAL TYPE 3: Very Strong RSI (regardless of streak)
            rsi = current_candle['rsi']
            if rsi >= self.params['rsi_very_overbought']:
                signal = {
                    'type': 'RSI_EXTREME',
                    'detail': f'RSI {rsi:.0f}',
                    'prediction': 'DOWN',
                    'bet': 'NO',
                    'confidence': 0.54
                }
            elif rsi <= self.params['rsi_very_oversold']:
                signal = {
                    'type': 'RSI_EXTREME',
                    'detail': f'RSI {rsi:.0f}',
                    'prediction': 'UP',
                    'bet': 'YES',
                    'confidence': 0.54
                }

            if signal is None:
                continue

            # Only trade if confidence >52%
            if signal['confidence'] < 0.52:
                continue

            # Execute
            bet_size = self.params['fixed_bet_size']
            prediction = signal['prediction']
            actual = next_candle['direction']
            win = (prediction == actual)

            if win:
                pnl = bet_size * (1 - self.params['polymarket_fee'])
            else:
                pnl = -bet_size * (1 + self.params['polymarket_fee'])

            capital += pnl
            daily_trades[current_date] += 1

            trades.append({
                'timestamp': current_candle.name,
                'signal_type': signal['type'],
                'detail': signal['detail'],
                'prediction': prediction,
                'polymarket_bet': signal['bet'],
                'actual': actual,
                'win': win,
                'confidence': signal['confidence'],
                'pnl': pnl,
                'capital': capital
            })

        self.trades_df = pd.DataFrame(trades)
        print(f"\n✅ Complete! {len(trades):,} trades")

        return self._analyze_results(initial_capital)

    def _get_streak(self, window):
        """Get streak info"""
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
        """Analyze results"""
        print(f"\n{'='*80}")
        print("📊 BALANCED STRATEGY RESULTS (2 YEARS)")
        print("="*80)

        total_trades = len(self.trades_df)
        wins = self.trades_df['win'].sum()
        win_rate = wins / total_trades

        final_capital = self.trades_df.iloc[-1]['capital']
        total_pnl = final_capital - initial_capital
        total_return = (total_pnl / initial_capital) * 100

        # Trades per day
        self.trades_df['date'] = pd.to_datetime(self.trades_df['timestamp']).dt.date
        unique_days = self.trades_df['date'].nunique()
        trades_per_day = total_trades / unique_days

        annualized = ((final_capital / initial_capital) ** (1/2) - 1) * 100

        print(f"Total Trades:        {total_trades:,}")
        print(f"Trades per Day:      {trades_per_day:.1f} {'✅' if trades_per_day >= 10 else '⚠️'}")
        print(f"Win Rate:            {win_rate*100:.2f}% {'✅' if win_rate > 0.52 else '⚠️'}")
        print()
        print(f"Initial Capital:     ${initial_capital:,.2f}")
        print(f"Final Capital:       ${final_capital:,.2f}")
        print(f"Total P&L:           ${total_pnl:+,.2f}")
        print(f"Total Return:        {total_return:+.2f}%")
        print(f"Annualized Return:   {annualized:+.2f}%")
        print()

        # Risk
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
        print(f"Profit Factor:       {profit_factor:.2f} {'✅' if profit_factor > 1.02 else '⚠️'}")
        print(f"Max Drawdown:        {max_dd:.2f}%")
        print()

        # By signal type
        print("📊 PERFORMANCE BY SIGNAL TYPE:")
        print("-"*80)
        by_signal = self.trades_df.groupby('signal_type').agg({
            'win': ['count', 'sum', 'mean'],
            'pnl': 'sum'
        }).round(2)
        by_signal.columns = ['Trades', 'Wins', 'Win Rate', 'Total P&L']
        by_signal['Win Rate'] = (by_signal['Win Rate'] * 100).round(1)
        by_signal['Avg P&L'] = (by_signal['Total P&L'] / by_signal['Trades']).round(2)
        print(by_signal.to_string())
        print()

        # Yearly
        self.trades_df['year'] = pd.to_datetime(self.trades_df['timestamp']).dt.year
        yearly = self.trades_df.groupby('year').agg({
            'win': ['count', 'mean'],
            'pnl': 'sum'
        }).round(2)
        yearly.columns = ['Trades', 'Win Rate', 'Yearly P&L']

        print("📅 YEARLY PERFORMANCE:")
        print("-"*80)
        print(yearly.to_string())
        print()

        # Monthly (last 12)
        self.trades_df['month'] = pd.to_datetime(self.trades_df['timestamp']).dt.to_period('M')
        monthly = self.trades_df.groupby('month').agg({
            'win': ['count', 'mean'],
            'pnl': 'sum'
        }).round(2)
        monthly.columns = ['Trades', 'Win Rate', 'Monthly P&L']

        print("📅 MONTHLY (Last 12):")
        print("-"*80)
        print(monthly.tail(12).to_string())

        # Save
        self.trades_df.to_csv('balanced_multi_strategy_2year.csv', index=False)
        print(f"\n💾 Saved to: balanced_multi_strategy_2year.csv")

        return {
            'total_trades': total_trades,
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'total_return': total_return,
            'annualized': annualized,
            'sharpe': sharpe,
            'profit_factor': profit_factor,
            'max_drawdown': max_dd
        }


def main():
    print("="*80)
    print("🎯 BALANCED MULTI-STRATEGY - 2 YEAR VALIDATION")
    print("="*80)
    print("\nGoal: 10+ trades/day AND >52% win rate")
    print("Approach: Quality + Quantity\n")

    strategy = BalancedMultiStrategy()
    strategy.generate_2year_data()
    results = strategy.backtest(initial_capital=10000)

    print(f"\n{'='*80}")
    print("✅ FINAL VERDICT")
    print("="*80)

    trades_ok = results['trades_per_day'] >= 10
    wr_ok = results['win_rate'] > 0.52
    pf_ok = results['profit_factor'] > 1.02

    print(f"Trades/Day: {results['trades_per_day']:.1f} {'✅' if trades_ok else '❌'}")
    print(f"Win Rate: {results['win_rate']*100:.1f}% {'✅' if wr_ok else '❌'}")
    print(f"Profit Factor: {results['profit_factor']:.2f} {'✅' if pf_ok else '❌'}")
    print(f"Annual Return: {results['annualized']:.1f}%")

    if trades_ok and wr_ok and pf_ok:
        print("\n🎉 STRATEGY VALIDATED - ALL CRITERIA MET!")
    else:
        print("\n⚠️  STRATEGY NEEDS REFINEMENT")


if __name__ == "__main__":
    main()
