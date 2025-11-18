"""
ENHANCED MULTI-STRATEGY - 2 YEAR BACKTEST
Target: 10+ trades per day across 4 strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


class EnhancedMultiStrategy2Y:
    """
    Multi-strategy system (2-year validation):
    1. Candle Streak Reversal (3+ candles)
    2. Volume Spike Fade
    3. RSI Extremes
    4. Bollinger Band Touch
    """

    def __init__(self):
        self.params = {
            'min_streak_length': 3,
            'max_streak_length': 8,
            'volume_spike_threshold': 2.0,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'bb_period': 20,
            'bb_std': 2.0,
            'fixed_bet_size': 100,
            'polymarket_fee': 0.02,
            'avoid_hours': [0, 1, 2, 3, 4, 5],
            'max_trades_per_day': 20,
            'daily_loss_limit': -800
        }
        self.df = None

    def generate_2year_data(self):
        """Generate 2 years of realistic BTC data"""
        np.random.seed(42)
        num_candles = 730 * 96  # 70,080 candles

        print(f"📊 Generating 2 years of data ({num_candles:,} candles)...")

        timestamps = []
        end_time = datetime.now()
        for i in range(num_candles):
            ts = end_time - timedelta(minutes=15 * (num_candles - i))
            timestamps.append(ts)

        # Generate realistic price
        base_price = 40000
        prices = [base_price]

        for i in range(1, num_candles):
            prev_price = prices[-1]

            # Market cycles (trending vs ranging)
            cycle_position = (i % 10000) / 10000
            if cycle_position < 0.3:  # Uptrend
                trend = 0.0003
            elif cycle_position < 0.6:  # Downtrend
                trend = -0.0003
            else:  # Ranging
                trend = 0

            # Mean reversion
            mean_revert = 0.02 * (base_price - prev_price) / base_price

            # Random walk
            shock = np.random.randn() * 0.004

            # Momentum
            if i > 1:
                prev_return = (prices[-1] - prices[-2]) / prices[-2]
                momentum = -0.02 * prev_return
            else:
                momentum = 0

            total_return = mean_revert + shock + momentum + trend
            new_price = prev_price * (1 + total_return)
            prices.append(new_price)

        # Generate OHLC
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            open_price = prices[i-1] if i > 0 else close

            base_vol = abs(np.random.randn()) * 0.002 * open_price

            # Volume spikes
            if np.random.random() < 0.08:
                volume = np.random.uniform(900, 1600)
                volatility = base_vol * 1.8
            else:
                volume = np.random.uniform(350, 750)
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
        print(f"📅 Period: {self.df.index[0]} to {self.df.index[-1]}")

    def _calculate_indicators(self):
        """Calculate all indicators"""
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

        # Bollinger Bands
        self.df['bb_middle'] = self.df['close'].rolling(self.params['bb_period']).mean()
        bb_std = self.df['close'].rolling(self.params['bb_period']).std()
        self.df['bb_upper'] = self.df['bb_middle'] + (bb_std * self.params['bb_std'])
        self.df['bb_lower'] = self.df['bb_middle'] - (bb_std * self.params['bb_std'])

        # Time
        self.df['hour'] = self.df.index.hour

        # Fill NaN
        self.df = self.df.bfill()

    def backtest(self, initial_capital=10000):
        """Run 2-year multi-strategy backtest"""
        print(f"\n{'='*80}")
        print("🔬 2-YEAR MULTI-STRATEGY BACKTEST")
        print("="*80)

        capital = initial_capital
        lookback = 30
        trades = []

        daily_trades = {}
        daily_pnl = {}

        print("\n⏳ Processing trades...")
        progress_interval = len(self.df) // 10

        for i in range(lookback, len(self.df) - 1):
            if i % progress_interval == 0:
                pct = (i / len(self.df)) * 100
                print(f"Progress: {i:,} / {len(self.df):,} ({pct:.1f}%)")

            current_date = self.df.index[i].date()
            current_candle = self.df.iloc[i]
            next_candle = self.df.iloc[i + 1]

            # Daily limits
            if current_date not in daily_trades:
                daily_trades[current_date] = 0
                daily_pnl[current_date] = 0

            if daily_trades[current_date] >= self.params['max_trades_per_day']:
                continue

            if daily_pnl[current_date] <= self.params['daily_loss_limit']:
                continue

            if current_candle['hour'] in self.params['avoid_hours']:
                continue

            # Check all strategies
            signals = []

            # Strategy 1: Streak
            window = self.df.iloc[i - lookback:i]
            streak_signal = self._check_streak(window, current_candle)
            if streak_signal:
                signals.append(streak_signal)

            # Strategy 2: Volume
            volume_signal = self._check_volume(current_candle)
            if volume_signal:
                signals.append(volume_signal)

            # Strategy 3: RSI
            rsi_signal = self._check_rsi(current_candle)
            if rsi_signal:
                signals.append(rsi_signal)

            # Strategy 4: Bollinger
            bb_signal = self._check_bollinger(current_candle)
            if bb_signal:
                signals.append(bb_signal)

            if not signals:
                continue

            # Prioritize by confidence
            signals.sort(key=lambda x: x['confidence'], reverse=True)
            signal = signals[0]

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
            daily_pnl[current_date] += pnl

            trades.append({
                'timestamp': current_candle.name,
                'strategy': signal['strategy'],
                'detail': signal['detail'],
                'prediction': prediction,
                'polymarket_bet': signal['polymarket_bet'],
                'actual': actual,
                'win': win,
                'confidence': signal['confidence'],
                'bet_size': bet_size,
                'pnl': pnl,
                'capital': capital
            })

        self.trades_df = pd.DataFrame(trades)
        print(f"\n✅ Backtest complete! {len(trades):,} trades executed")

        return self._analyze_results(initial_capital)

    def _check_streak(self, window, current_candle):
        """Check streak strategy"""
        if len(window) == 0:
            return None

        current_dir = window.iloc[-1]['direction']
        if current_dir == "NEUTRAL":
            return None

        streak_len = 1
        for i in range(len(window) - 2, -1, -1):
            if window.iloc[i]['direction'] == current_dir:
                streak_len += 1
            else:
                break

        if streak_len < self.params['min_streak_length']:
            return None
        if streak_len > self.params['max_streak_length']:
            return None

        # Probability increases with streak length
        probability = min(0.52 + (streak_len - 3) * 0.015, 0.58)

        if current_dir == "UP":
            prediction = "DOWN"
            bet = "NO"
        else:
            prediction = "UP"
            bet = "YES"

        return {
            'strategy': 'STREAK',
            'detail': f'{streak_len} {current_dir}',
            'prediction': prediction,
            'polymarket_bet': bet,
            'confidence': probability
        }

    def _check_volume(self, current_candle):
        """Check volume spike"""
        if current_candle['volume_ratio'] < self.params['volume_spike_threshold']:
            return None

        current_dir = current_candle['direction']
        if current_dir == "NEUTRAL":
            return None

        if current_dir == "UP":
            return {
                'strategy': 'VOLUME',
                'detail': f'{current_candle["volume_ratio"]:.1f}x',
                'prediction': 'DOWN',
                'polymarket_bet': 'NO',
                'confidence': 0.53
            }
        else:
            return {
                'strategy': 'VOLUME',
                'detail': f'{current_candle["volume_ratio"]:.1f}x',
                'prediction': 'UP',
                'polymarket_bet': 'YES',
                'confidence': 0.53
            }

    def _check_rsi(self, current_candle):
        """Check RSI extremes"""
        rsi = current_candle['rsi']

        if rsi > self.params['rsi_overbought']:
            return {
                'strategy': 'RSI',
                'detail': f'{rsi:.0f} OB',
                'prediction': 'DOWN',
                'polymarket_bet': 'NO',
                'confidence': 0.52
            }
        elif rsi < self.params['rsi_oversold']:
            return {
                'strategy': 'RSI',
                'detail': f'{rsi:.0f} OS',
                'prediction': 'UP',
                'polymarket_bet': 'YES',
                'confidence': 0.52
            }

        return None

    def _check_bollinger(self, current_candle):
        """Check Bollinger band touch"""
        close = current_candle['close']
        bb_upper = current_candle['bb_upper']
        bb_lower = current_candle['bb_lower']

        if close >= bb_upper * 0.995:
            return {
                'strategy': 'BOLLINGER',
                'detail': 'Upper',
                'prediction': 'DOWN',
                'polymarket_bet': 'NO',
                'confidence': 0.51
            }
        elif close <= bb_lower * 1.005:
            return {
                'strategy': 'BOLLINGER',
                'detail': 'Lower',
                'prediction': 'UP',
                'polymarket_bet': 'YES',
                'confidence': 0.51
            }

        return None

    def _analyze_results(self, initial_capital):
        """Analyze 2-year results"""
        print(f"\n{'='*80}")
        print("📊 2-YEAR MULTI-STRATEGY RESULTS")
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

        # Annualized return
        years = 2.0
        annualized_return = ((final_capital / initial_capital) ** (1/years) - 1) * 100

        print(f"Total Trades:        {total_trades:,}")
        print(f"Trades per Day:      {trades_per_day:.1f} {'✅' if trades_per_day >= 10 else '⚠️'}")
        print(f"Win Rate:            {win_rate*100:.2f}%")
        print()
        print(f"Initial Capital:     ${initial_capital:,.2f}")
        print(f"Final Capital:       ${final_capital:,.2f}")
        print(f"Total P&L:           ${total_pnl:+,.2f}")
        print(f"Total Return:        {total_return:+.2f}%")
        print(f"Annualized Return:   {annualized_return:+.2f}%")
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

        # By strategy
        print("📊 PERFORMANCE BY STRATEGY:")
        print("-"*80)
        by_strategy = self.trades_df.groupby('strategy').agg({
            'win': ['count', 'sum', 'mean'],
            'pnl': 'sum'
        }).round(2)
        by_strategy.columns = ['Trades', 'Wins', 'Win Rate', 'Total P&L']
        by_strategy['Win Rate'] = (by_strategy['Win Rate'] * 100).round(1)
        by_strategy['Avg P&L'] = (by_strategy['Total P&L'] / by_strategy['Trades']).round(2)
        print(by_strategy.to_string())
        print()

        # Yearly
        self.trades_df['year'] = pd.to_datetime(self.trades_df['timestamp']).dt.year
        yearly = self.trades_df.groupby('year').agg({
            'win': ['count', 'mean'],
            'pnl': 'sum'
        }).round(2)
        yearly.columns = ['Trades', 'Win Rate', 'Yearly P&L']

        print("📅 YEARLY BREAKDOWN:")
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
        self.trades_df.to_csv('enhanced_multi_strategy_2year_results.csv', index=False)
        print(f"\n💾 Saved to: enhanced_multi_strategy_2year_results.csv")

        return {
            'total_trades': total_trades,
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'profit_factor': profit_factor
        }


def main():
    print("="*80)
    print("🚀 ENHANCED MULTI-STRATEGY - 2 YEAR VALIDATION")
    print("="*80)
    print("\nTarget: 10+ trades per day")
    print("Duration: 730 days (2 years)")
    print("Strategies: Streaks (3+), Volume, RSI, Bollinger\n")

    strategy = EnhancedMultiStrategy2Y()
    strategy.generate_2year_data()
    results = strategy.backtest(initial_capital=10000)

    print(f"\n{'='*80}")
    print("✅ 2-YEAR MULTI-STRATEGY BACKTEST COMPLETE")
    print("="*80)
    print(f"\nFINAL VERDICT:")
    print(f"  Trades/Day: {results['trades_per_day']:.1f} {'✅ TARGET MET' if results['trades_per_day'] >= 10 else '⚠️ BELOW TARGET'}")
    print(f"  Win Rate: {results['win_rate']*100:.1f}%")
    print(f"  Annual Return: {results['annualized_return']:.1f}%")
    print(f"  Max DD: {results['max_drawdown']:.1f}%")


if __name__ == "__main__":
    main()
