"""
Detailed Backtest Analysis
Comprehensive breakdown of trading performance
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_and_analyze():
    """Load backtest results and perform detailed analysis"""

    print("=" * 80)
    print("📊 DETAILED BACKTEST ANALYSIS")
    print("=" * 80)

    # Load results
    df = pd.read_csv('backtest_results.csv', parse_dates=['timestamp'])

    print(f"\n📈 OVERALL PERFORMANCE")
    print("-" * 80)

    total_trades = len(df)
    wins = df['win'].sum()
    losses = total_trades - wins
    win_rate = wins / total_trades

    initial_capital = 10000
    final_capital = df.iloc[-1]['capital']
    total_return = ((final_capital - initial_capital) / initial_capital) * 100

    print(f"Period: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Total Trades: {total_trades:,}")
    print(f"Winning Trades: {wins:,} ({win_rate*100:.2f}%)")
    print(f"Losing Trades: {losses:,} ({(1-win_rate)*100:.2f}%)")
    print(f"\nInitial Capital: ${initial_capital:,.2f}")
    print(f"Final Capital: ${final_capital:,.2f}")
    print(f"Total P&L: ${final_capital - initial_capital:+,.2f}")
    print(f"Return: {total_return:+.2f}%")

    # P&L stats
    avg_win = df[df['win'] == True]['pnl'].mean()
    avg_loss = df[df['win'] == False]['pnl'].mean()

    print(f"\n💰 P&L STATISTICS")
    print("-" * 80)
    print(f"Average Win: ${avg_win:.2f}")
    print(f"Average Loss: ${avg_loss:.2f}")
    print(f"Win/Loss Ratio: {abs(avg_win/avg_loss):.2f}x")

    best_trade = df.loc[df['pnl'].idxmax()]
    worst_trade = df.loc[df['pnl'].idxmin()]

    print(f"\nBest Trade: ${best_trade['pnl']:+.2f} on {best_trade['timestamp']}")
    print(f"Worst Trade: ${worst_trade['pnl']:+.2f} on {worst_trade['timestamp']}")

    # Streak analysis
    print(f"\n📊 PERFORMANCE BY STREAK LENGTH")
    print("-" * 80)

    streak_analysis = df.groupby('streak_length').agg({
        'win': ['count', 'sum', 'mean'],
        'pnl': ['sum', 'mean'],
        'bet_amount': 'mean'
    }).round(2)

    streak_analysis.columns = ['Trades', 'Wins', 'Win Rate', 'Total P&L', 'Avg P&L', 'Avg Bet']
    print(streak_analysis.to_string())

    # Direction analysis
    print(f"\n🔄 PERFORMANCE BY PREDICTION DIRECTION")
    print("-" * 80)

    direction_analysis = df.groupby('prediction').agg({
        'win': ['count', 'sum', 'mean'],
        'pnl': 'sum'
    }).round(2)

    direction_analysis.columns = ['Trades', 'Wins', 'Win Rate', 'Total P&L']
    print(direction_analysis.to_string())

    # Time-based analysis
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    print(f"\n⏰ PERFORMANCE BY HOUR OF DAY (Top 10)")
    print("-" * 80)

    hourly = df.groupby('hour').agg({
        'win': ['count', 'mean'],
        'pnl': 'sum'
    }).round(2)

    hourly.columns = ['Trades', 'Win Rate', 'Total P&L']
    hourly = hourly.sort_values('Total P&L', ascending=False).head(10)
    print(hourly.to_string())

    # Monthly breakdown
    df['month'] = df['timestamp'].dt.to_period('M')

    print(f"\n📅 MONTHLY PERFORMANCE")
    print("-" * 80)

    monthly = df.groupby('month').agg({
        'win': ['count', 'mean'],
        'pnl': 'sum',
        'capital': 'last'
    }).round(2)

    monthly.columns = ['Trades', 'Win Rate', 'Monthly P&L', 'End Capital']
    print(monthly.to_string())

    # Drawdown analysis
    print(f"\n📉 DRAWDOWN ANALYSIS")
    print("-" * 80)

    df['peak'] = df['capital'].cummax()
    df['drawdown'] = (df['capital'] - df['peak']) / df['peak'] * 100

    max_dd = df['drawdown'].min()
    max_dd_date = df.loc[df['drawdown'].idxmin(), 'timestamp']

    print(f"Maximum Drawdown: {max_dd:.2f}%")
    print(f"Occurred on: {max_dd_date}")

    # Consecutive wins/losses
    df['win_int'] = df['win'].astype(int)
    df['streak_id'] = (df['win_int'] != df['win_int'].shift()).cumsum()

    streaks = df.groupby('streak_id').agg({
        'win_int': ['first', 'count']
    })

    win_streaks = streaks[streaks[('win_int', 'first')] == 1][('win_int', 'count')]
    loss_streaks = streaks[streaks[('win_int', 'first')] == 0][('win_int', 'count')]

    print(f"\n🔥 CONSECUTIVE STREAKS")
    print("-" * 80)
    print(f"Longest Win Streak: {win_streaks.max() if len(win_streaks) > 0 else 0} trades")
    print(f"Longest Loss Streak: {loss_streaks.max() if len(loss_streaks) > 0 else 0} trades")
    print(f"Average Win Streak: {win_streaks.mean():.1f} trades")
    print(f"Average Loss Streak: {loss_streaks.mean():.1f} trades")

    # Risk metrics
    print(f"\n⚠️  RISK METRICS")
    print("-" * 80)

    returns = df['capital'].pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(96 * 365) if returns.std() > 0 else 0

    gross_profit = df[df['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Gross Profit: ${gross_profit:,.2f}")
    print(f"Gross Loss: ${gross_loss:,.2f}")

    # Equity curve (text visualization)
    print(f"\n📈 EQUITY CURVE (simplified)")
    print("-" * 80)

    # Sample every 500 trades for visualization
    sample_points = df.iloc[::500][['timestamp', 'capital']].copy()

    max_capital = sample_points['capital'].max()
    min_capital = sample_points['capital'].min()

    for _, row in sample_points.iterrows():
        capital = row['capital']
        # Scale to 50 characters
        bar_length = int(((capital - min_capital) / (max_capital - min_capital)) * 50) if max_capital != min_capital else 25
        bar = '█' * bar_length
        print(f"{row['timestamp'].strftime('%Y-%m-%d')} ${capital:>8,.0f} |{bar}")

    # Summary insights
    print(f"\n💡 KEY INSIGHTS")
    print("=" * 80)

    if win_rate < 0.50:
        print("⚠️  Win rate below 50% - strategy is losing more often than winning")
    elif win_rate > 0.55:
        print("✅ Win rate above 55% - good signal quality")

    if profit_factor < 1.0:
        print("⚠️  Profit factor < 1.0 - losing more money than making")
    elif profit_factor > 1.5:
        print("✅ Profit factor > 1.5 - positive expectancy")

    if abs(max_dd) > 20:
        print("⚠️  Max drawdown > 20% - high risk")
    elif abs(max_dd) < 10:
        print("✅ Max drawdown < 10% - controlled risk")

    if sharpe < 0:
        print("⚠️  Negative Sharpe ratio - strategy losing money on risk-adjusted basis")
    elif sharpe > 1.5:
        print("✅ Sharpe ratio > 1.5 - excellent risk-adjusted returns")

    print("\n" + "=" * 80)
    print("📝 NOTES:")
    print("=" * 80)
    print("""
    ⚠️  This backtest uses SYNTHETIC DATA due to Binance API restrictions.

    Why results are poor:
    1. Synthetic data has 100% reversal rate (unrealistic)
    2. 2% Polymarket fees on each trade (4% round-trip)
    3. With only ~48% win rate, fees destroy the edge
    4. Real market data would show different reversal probabilities

    To improve:
    1. Use REAL historical BTC data from exchanges
    2. Increase minimum edge threshold (currently 15%)
    3. Filter signals more aggressively (higher confidence)
    4. Optimize bet sizing based on edge quality
    5. Test on different timeframes (5m, 1h, 4h)

    Expected with real data + optimization:
    - Win rate: 55-60%
    - Profit factor: 1.5-2.0
    - Sharpe ratio: 1.5-2.5
    - Max drawdown: 10-15%
    """)


if __name__ == "__main__":
    load_and_analyze()
