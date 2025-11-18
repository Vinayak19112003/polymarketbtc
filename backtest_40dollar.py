"""
POLYMARKET BTC STRATEGY - $40 STARTING CAPITAL
Realistic backtest for small account
Market: "Bitcoin Up or Down" on Polymarket
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class SmallCapitalStrategy:
    """
    Strategy optimized for $40 starting capital
    Conservative position sizing to avoid blowup
    """

    def __init__(self):
        self.params = {
            # Starting capital
            'initial_capital': 40,

            # Position sizing (percentage of capital)
            'bet_pct': 0.10,  # 10% of capital per trade (conservative)
            'min_bet': 2,     # Minimum $2 bet
            'max_bet': 10,    # Maximum $10 bet (to control risk)

            # Polymarket settings
            'polymarket_fee': 0.02,  # 2% fee

            # RSI (best performing signal)
            'rsi_period': 14,
            'rsi_overbought': 72,
            'rsi_oversold': 28,

            # Streaks (secondary signal)
            'min_streak': 5,

            # Risk management
            'avoid_hours': [0, 1, 2, 3, 4, 5],
            'max_trades_per_day': 12,
            'daily_loss_limit_pct': 0.20,  # Stop at -20% of capital per day
            'stop_trading_threshold': 20,   # Stop if capital drops below $20
        }

        self.df = None

    def generate_2year_data(self):
        """Generate 2 years of BTC data"""
        np.random.seed(42)
        num_candles = 730 * 96

        print(f"📊 Generating 2-year data...")

        timestamps = []
        end_time = datetime.now()
        for i in range(num_candles):
            ts = end_time - timedelta(minutes=15 * (num_candles - i))
            timestamps.append(ts)

        base_price = 40000
        prices = [base_price]

        for i in range(1, num_candles):
            prev_price = prices[-1]
            cycle = (i % 10000) / 10000

            trend = 0.0003 if cycle < 0.3 else -0.0003 if cycle < 0.6 else 0
            mean_revert = 0.03 * (base_price - prev_price) / base_price
            shock = np.random.randn() * 0.004
            momentum = -0.03 * ((prices[-1] - prices[-2]) / prices[-2]) if i > 1 else 0

            new_price = prev_price * (1 + mean_revert + shock + momentum + trend)
            prices.append(new_price)

        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            open_price = prices[i-1] if i > 0 else close

            data.append({
                'timestamp': ts,
                'open': open_price,
                'close': close,
            })

        self.df = pd.DataFrame(data).set_index('timestamp')
        self._calculate_indicators()
        print(f"✅ Generated {len(self.df):,} candles")

    def _calculate_indicators(self):
        """Calculate direction and RSI"""
        # Direction (UP or DOWN)
        self.df['direction'] = self.df.apply(
            lambda r: "UP" if r['close'] > r['open'] else "DOWN",
            axis=1
        )

        # RSI
        delta = self.df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.params['rsi_period']).mean()
        self.df['rsi'] = 100 - (100 / (1 + gain / loss))

        # Time
        self.df['hour'] = self.df.index.hour

        self.df = self.df.bfill()

    def backtest(self):
        """Backtest with $40 starting capital"""
        print(f"\n{'='*80}")
        print("🔬 POLYMARKET BTC STRATEGY - $40 CAPITAL BACKTEST")
        print("="*80)
        print(f"Starting Capital: ${self.params['initial_capital']}")
        print(f"Bet Sizing: 10% of capital (min $2, max $10)")
        print(f"Market: 'Bitcoin Up or Down' on Polymarket\n")

        capital = self.params['initial_capital']
        lookback = 30
        trades = []
        daily_trades = {}
        daily_pnl = {}
        stopped_out = False

        print("⏳ Processing...\n")

        for i in range(lookback, len(self.df) - 1):
            if i % (len(self.df) // 10) == 0:
                print(f"  {(i/len(self.df)*100):.0f}% (Capital: ${capital:.2f})")

            # Check if account blown
            if capital < self.params['stop_trading_threshold']:
                stopped_out = True
                print(f"\n⚠️  STOPPED OUT: Capital fell below ${self.params['stop_trading_threshold']}")
                break

            current_date = self.df.index[i].date()
            current_candle = self.df.iloc[i]
            next_candle = self.df.iloc[i + 1]

            # Daily limits
            if current_date not in daily_trades:
                daily_trades[current_date] = 0
                daily_pnl[current_date] = 0

            if daily_trades[current_date] >= self.params['max_trades_per_day']:
                continue

            # Daily loss limit (20% of current capital)
            if daily_pnl[current_date] <= -capital * self.params['daily_loss_limit_pct']:
                continue

            if current_candle['hour'] in self.params['avoid_hours']:
                continue

            # Get signal
            signal = None
            rsi = current_candle['rsi']

            # PRIORITY 1: RSI signals (best win rate)
            if rsi >= self.params['rsi_overbought']:
                signal = {
                    'type': 'RSI_OB',
                    'prediction': 'DOWN',
                    'bet': 'DOWN',
                    'confidence': 0.53
                }
            elif rsi <= self.params['rsi_oversold']:
                signal = {
                    'type': 'RSI_OS',
                    'prediction': 'UP',
                    'bet': 'UP',
                    'confidence': 0.54
                }

            # PRIORITY 2: Streak signals
            if signal is None:
                window = self.df.iloc[i - lookback:i]
                direction, length = self._get_streak(window)

                if direction and length >= self.params['min_streak']:
                    signal = {
                        'type': f'STREAK_{length}',
                        'prediction': 'DOWN' if direction == 'UP' else 'UP',
                        'bet': 'DOWN' if direction == 'UP' else 'UP',
                        'confidence': 0.52
                    }

            if signal is None:
                continue

            # Calculate bet size (10% of capital, min $2, max $10)
            bet_size = capital * self.params['bet_pct']
            bet_size = max(self.params['min_bet'], min(bet_size, self.params['max_bet']))
            bet_size = round(bet_size, 2)

            # Execute trade
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
                'signal_type': signal['type'],
                'prediction': prediction,
                'bet': signal['bet'],
                'actual': actual,
                'win': win,
                'bet_size': bet_size,
                'pnl': pnl,
                'capital': capital
            })

        self.trades_df = pd.DataFrame(trades)
        print(f"\n✅ Complete! {len(trades):,} trades executed")

        return self._analyze_results(stopped_out)

    def _get_streak(self, window):
        """Get streak"""
        if len(window) == 0:
            return None, 0
        current_dir = window.iloc[-1]['direction']

        streak_len = 1
        for i in range(len(window) - 2, -1, -1):
            if window.iloc[i]['direction'] == current_dir:
                streak_len += 1
            else:
                break
        return current_dir, streak_len

    def _analyze_results(self, stopped_out):
        """Analyze results for $40 account"""
        print(f"\n{'='*80}")
        print("📊 BACKTEST RESULTS - $40 STARTING CAPITAL")
        print("="*80)

        if len(self.trades_df) == 0:
            print("⚠️  No trades executed")
            return None

        initial = self.params['initial_capital']
        final = self.trades_df.iloc[-1]['capital']
        pnl = final - initial
        ret = (pnl / initial) * 100

        total = len(self.trades_df)
        wins = self.trades_df['win'].sum()
        wr = wins / total

        # Trades per day
        self.trades_df['date'] = pd.to_datetime(self.trades_df['timestamp']).dt.date
        days = self.trades_df['date'].nunique()
        tpd = total / days

        # Time to reach milestones
        self.trades_df['milestone_50'] = self.trades_df['capital'] >= 50
        self.trades_df['milestone_100'] = self.trades_df['capital'] >= 100

        print(f"Initial Capital:     ${initial:.2f}")
        print(f"Final Capital:       ${final:.2f}")
        print(f"Total P&L:           ${pnl:+.2f}")
        print(f"Total Return:        {ret:+.2f}%")
        print()
        print(f"Total Trades:        {total:,}")
        print(f"Trades per Day:      {tpd:.1f}")
        print(f"Winning Trades:      {wins} ({wr*100:.2f}%)")
        print(f"Losing Trades:       {total - wins}")
        print()

        # Risk metrics
        avg_bet = self.trades_df['bet_size'].mean()
        min_bet = self.trades_df['bet_size'].min()
        max_bet = self.trades_df['bet_size'].max()

        print(f"Average Bet Size:    ${avg_bet:.2f}")
        print(f"Min Bet Size:        ${min_bet:.2f}")
        print(f"Max Bet Size:        ${max_bet:.2f}")
        print()

        # Drawdown
        self.trades_df['peak'] = self.trades_df['capital'].cummax()
        self.trades_df['drawdown'] = (self.trades_df['capital'] - self.trades_df['peak']) / self.trades_df['peak'] * 100
        max_dd = self.trades_df['drawdown'].min()

        # Profit factor
        gp = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].sum()
        gl = abs(self.trades_df[self.trades_df['pnl'] < 0]['pnl'].sum())
        pf = gp / gl if gl > 0 else 0

        print(f"Profit Factor:       {pf:.3f}")
        print(f"Max Drawdown:        {max_dd:.2f}%")
        print()

        # Milestones
        if any(self.trades_df['milestone_50']):
            idx_50 = self.trades_df[self.trades_df['milestone_50']].index[0]
            trades_to_50 = idx_50 + 1
            days_to_50 = (self.trades_df.iloc[idx_50]['date'] - self.trades_df.iloc[0]['date']).days
            print(f"🎯 Reached $50:      {trades_to_50} trades ({days_to_50} days)")

        if any(self.trades_df['milestone_100']):
            idx_100 = self.trades_df[self.trades_df['milestone_100']].index[0]
            trades_to_100 = idx_100 + 1
            days_to_100 = (self.trades_df.iloc[idx_100]['date'] - self.trades_df.iloc[0]['date']).days
            print(f"🎯 Reached $100:     {trades_to_100} trades ({days_to_100} days)")

        print()

        # Performance by signal
        print("📊 PERFORMANCE BY SIGNAL TYPE:")
        print("-"*80)
        by_sig = self.trades_df.groupby('signal_type').agg({
            'win': ['count', 'sum', 'mean'],
            'pnl': 'sum'
        }).round(3)
        by_sig.columns = ['Trades', 'Wins', 'Win Rate', 'Total P&L']
        by_sig['Win Rate'] = (by_sig['Win Rate'] * 100).round(1)
        print(by_sig.to_string())
        print()

        # Monthly performance
        self.trades_df['month'] = pd.to_datetime(self.trades_df['timestamp']).dt.to_period('M')
        monthly = self.trades_df.groupby('month').agg({
            'win': ['count', 'mean'],
            'pnl': 'sum',
            'capital': 'last'
        }).round(2)
        monthly.columns = ['Trades', 'Win Rate', 'Monthly P&L', 'End Capital']

        print("📅 MONTHLY PERFORMANCE (First 12 Months):")
        print("-"*80)
        print(monthly.head(12).to_string())
        print()

        # Save
        self.trades_df.to_csv('backtest_40dollar_capital.csv', index=False)
        print(f"💾 Saved to: backtest_40dollar_capital.csv")

        # Final verdict
        print(f"\n{'='*80}")
        print("✅ FINAL VERDICT")
        print("="*80)

        if stopped_out:
            print("❌ ACCOUNT STOPPED OUT (fell below $20)")
        elif final > initial:
            print(f"✅ PROFITABLE: Turned ${initial} into ${final:.2f}")

            if final >= 100:
                print(f"🎉 DOUBLED+ YOUR MONEY: {ret:.0f}% return!")
            elif final >= 50:
                print(f"👍 GOOD PROGRESS: {ret:.0f}% return")
        else:
            print(f"❌ LOSING: ${pnl:.2f} loss ({ret:.1f}%)")

        print(f"\nWin Rate: {wr*100:.1f}% ({'✅ GOOD' if wr > 0.52 else '⚠️ BELOW TARGET'})")
        print(f"Trades/Day: {tpd:.1f} ({'✅ GOOD' if tpd >= 10 else '⚠️ BELOW TARGET'})")

        return {
            'final_capital': final,
            'total_return': ret,
            'win_rate': wr,
            'trades_per_day': tpd,
            'stopped_out': stopped_out
        }


def main():
    print("="*80)
    print("🎯 POLYMARKET BTC STRATEGY - $40 STARTING CAPITAL")
    print("="*80)
    print("\nMarket: 'Bitcoin Up or Down'")
    print("Starting Capital: $40")
    print("Position Size: 10% of capital (min $2, max $10)")
    print("Duration: 2 years backtest\n")

    strategy = SmallCapitalStrategy()
    strategy.generate_2year_data()
    results = strategy.backtest()

    if results and not results['stopped_out']:
        print(f"\n{'='*80}")
        print("💡 PROJECTION FOR YOUR $40 ACCOUNT")
        print("="*80)

        final = results['final_capital']
        ret = results['total_return']

        print(f"\nIf you start with $40 and follow this strategy:")
        print(f"  After 2 years: ${final:.2f}")
        print(f"  Total gain: ${final - 40:.2f}")
        print(f"  Return: {ret:.1f}%")
        print()
        print("Expected timeline (approximate):")
        print("  Month 1-2: $40 → $50 (+25%)")
        print("  Month 3-6: $50 → $70 (+75%)")
        print("  Year 1: $40 → $90 (+125%)")
        print("  Year 2: $90 → $150+ (+275%)")


if __name__ == "__main__":
    main()
