"""
POLYMARKET 15M BTC PREDICTOR
For markets like: "Will next BTC 15m candle be BULLISH or BEARISH?"

YES = Bullish (green candle, close > open)
NO = Bearish (red candle, close < open)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from btc_streak_analysis import BTCStreakAnalyzer


class Polymarket15mPredictor:
    """Predict next 15m candle direction for Polymarket YES/NO markets"""

    def __init__(self):
        self.analyzer = BTCStreakAnalyzer(interval='15m', lookback_days=90)
        self.reversal_probabilities = {}
        self.current_streak = None
        self.current_streak_length = 0

    def train(self):
        """Analyze historical data to build reversal probability table"""
        print("=" * 80)
        print("🎯 POLYMARKET 15M BTC PREDICTOR - TRAINING")
        print("=" * 80)

        # Fetch and analyze data
        if not self.analyzer.fetch_data():
            return False

        self.analyzer.calculate_direction()
        streak_df = self.analyzer.analyze_streaks()
        reversal_stats = self.analyzer.calculate_reversal_probability(streak_df)

        # Build lookup table
        for _, row in reversal_stats.iterrows():
            key = (row['direction'], row['streak_length'])
            self.reversal_probabilities[key] = {
                'reversal_prob': row['reversal_prob'],
                'sample_size': row['total']
            }

        print(f"\n✅ Training complete!")
        print(f"📊 Learned reversal probabilities for {len(self.reversal_probabilities)} patterns")

        return True

    def predict_next_candle(self, current_streak_direction, current_streak_length):
        """
        Predict next candle direction based on current streak

        Args:
            current_streak_direction: "UP" or "DOWN"
            current_streak_length: Number of consecutive candles

        Returns:
            dict with prediction, probability, and Polymarket bet recommendation
        """
        key = (current_streak_direction, current_streak_length)

        # Look up reversal probability
        if key in self.reversal_probabilities:
            data = self.reversal_probabilities[key]
            reversal_prob = data['reversal_prob']
            sample_size = data['sample_size']
        else:
            # Default to 50/50 if no data
            reversal_prob = 0.50
            sample_size = 0

        # Determine prediction
        if reversal_prob > 0.50:
            # More likely to reverse
            if current_streak_direction == "UP":
                prediction = "BEARISH"
                polymarket_bet = "NO"  # Bet NO on bullish
            else:
                prediction = "BULLISH"
                polymarket_bet = "YES"  # Bet YES on bullish
            confidence = reversal_prob
        else:
            # More likely to continue
            if current_streak_direction == "UP":
                prediction = "BULLISH"
                polymarket_bet = "YES"  # Bet YES on bullish
            else:
                prediction = "BEARISH"
                polymarket_bet = "NO"  # Bet NO on bullish
            confidence = 1 - reversal_prob

        # Calculate edge (assuming Polymarket is at 50/50)
        market_price = 0.50
        edge = confidence - market_price

        # Determine bet quality
        if edge < 0.05 or sample_size < 10:
            quality = "SKIP"
            recommendation = "Don't bet - insufficient edge or data"
        elif edge >= 0.15 and sample_size >= 50:
            quality = "A+"
            recommendation = "STRONG BET - High edge & confidence"
        elif edge >= 0.10 and sample_size >= 20:
            quality = "A"
            recommendation = "GOOD BET - Moderate edge"
        elif edge >= 0.05 and sample_size >= 10:
            quality = "B"
            recommendation = "WEAK BET - Small edge"
        else:
            quality = "C"
            recommendation = "RISKY BET - Low confidence"

        return {
            'prediction': prediction,
            'polymarket_bet': polymarket_bet,
            'confidence': confidence,
            'edge': edge,
            'quality': quality,
            'recommendation': recommendation,
            'sample_size': sample_size,
            'reversal_prob': reversal_prob,
            'current_streak': f"{current_streak_length} consecutive {current_streak_direction}"
        }

    def print_prediction(self, result):
        """Pretty print prediction result"""
        print("\n" + "=" * 80)
        print("🔮 NEXT CANDLE PREDICTION")
        print("=" * 80)

        print(f"\n📊 Current Market State:")
        print(f"   Streak: {result['current_streak']}")
        print(f"   Sample Size: {result['sample_size']} historical occurrences")
        print(f"   Reversal Probability: {result['reversal_prob']*100:.1f}%")

        print(f"\n🎯 Prediction:")
        print(f"   Next Candle: {result['prediction']}")
        print(f"   Confidence: {result['confidence']*100:.1f}%")

        print(f"\n💰 Polymarket Recommendation:")
        print(f"   Market: 'Will next 15m BTC candle be BULLISH?'")
        print(f"   Bet: {result['polymarket_bet']}")
        print(f"   Edge: {result['edge']*100:+.1f}% (vs 50/50)")
        print(f"   Quality: {result['quality']}")
        print(f"   Action: {result['recommendation']}")

        # Position sizing suggestion
        if result['quality'] in ['A+', 'A']:
            suggested_size = min(result['edge'] * 500, 100)  # Kelly-ish
            print(f"\n💵 Suggested Position Size: ${suggested_size:.0f}")
            print(f"   (Based on {result['edge']*100:.1f}% edge)")

        print("\n" + "=" * 80)


def demo_predictions():
    """Demo showing predictions for different scenarios"""
    print("=" * 80)
    print("🚀 POLYMARKET 15M BTC PREDICTOR - DEMO")
    print("=" * 80)

    predictor = Polymarket15mPredictor()

    # Train on historical data
    if not predictor.train():
        return

    print("\n" + "=" * 80)
    print("📋 EXAMPLE PREDICTIONS FOR DIFFERENT SCENARIOS")
    print("=" * 80)

    scenarios = [
        ("UP", 1, "1 green candle - What's next?"),
        ("DOWN", 1, "1 red candle - What's next?"),
        ("UP", 3, "3 green candles in a row - Reversal coming?"),
        ("DOWN", 3, "3 red candles in a row - Reversal coming?"),
        ("UP", 5, "5 green candles in a row - Strong reversal signal?"),
        ("DOWN", 5, "5 red candles in a row - Strong reversal signal?"),
    ]

    for direction, length, description in scenarios:
        print(f"\n{'─' * 80}")
        print(f"📌 SCENARIO: {description}")
        print(f"{'─' * 80}")

        result = predictor.predict_next_candle(direction, length)
        predictor.print_prediction(result)


def real_time_example():
    """Example of how to use in real-time"""
    print("\n\n" + "=" * 80)
    print("💡 HOW TO USE IN REAL-TIME")
    print("=" * 80)

    example_code = '''
# Step 1: Initialize and train
predictor = Polymarket15mPredictor()
predictor.train()

# Step 2: Get current market state (from live data)
current_streak_direction = "UP"   # Last 3 candles were green
current_streak_length = 3

# Step 3: Get prediction
result = predictor.predict_next_candle(
    current_streak_direction,
    current_streak_length
)

# Step 4: Check if worth betting
if result['quality'] in ['A+', 'A']:
    print(f"PLACE BET: {result['polymarket_bet']}")
    print(f"Market: 'Will next 15m BTC candle be BULLISH?'")
    print(f"Expected value: +{result['edge']*100:.1f}%")
else:
    print("SKIP - Not enough edge")

# Step 5: Place bet on Polymarket
# (Use polymarket_trader.py for actual execution)
'''

    print(example_code)

    print("\n" + "=" * 80)
    print("🎯 POLYMARKET MARKET NAMES TO LOOK FOR:")
    print("=" * 80)
    print("""
    Exact market names on Polymarket might be:

    ✅ "Will BTC close higher in the next 15 minutes?"
    ✅ "Will the next BTC 15m candle be green?"
    ✅ "BTC 15m candle outcome: Bullish or Bearish?"
    ✅ "Will BTC price increase in next 15 min?"

    For ALL of these:
    - If we predict BULLISH → Bet YES
    - If we predict BEARISH → Bet NO
    """)


def create_signal_table():
    """Create a quick reference signal table"""
    print("\n" + "=" * 80)
    print("📊 QUICK REFERENCE: TRADING SIGNALS")
    print("=" * 80)

    predictor = Polymarket15mPredictor()
    if not predictor.train():
        return

    print("\n" + "┌" + "─" * 78 + "┐")
    print("│" + " " * 20 + "POLYMARKET BETTING GUIDE" + " " * 34 + "│")
    print("├" + "─" * 78 + "┤")
    print("│ Current Streak        │ Predict  │ Polymarket Bet │ Edge    │ Quality │")
    print("├" + "─" * 78 + "┤")

    test_cases = [
        ("UP", 1), ("DOWN", 1),
        ("UP", 2), ("DOWN", 2),
        ("UP", 3), ("DOWN", 3),
        ("UP", 4), ("DOWN", 4),
        ("UP", 5), ("DOWN", 5),
        ("UP", 6), ("DOWN", 6),
    ]

    for direction, length in test_cases:
        result = predictor.predict_next_candle(direction, length)
        streak_str = f"{length} {direction} candles"
        bet_str = f"Bet {result['polymarket_bet']}"
        edge_str = f"{result['edge']*100:+.1f}%"

        print(f"│ {streak_str:<21} │ {result['prediction']:<8} │ {bet_str:<14} │ {edge_str:<7} │ {result['quality']:<7} │")

    print("└" + "─" * 78 + "┘")

    print("""

    HOW TO READ THIS TABLE:

    1. Check current BTC chart - count consecutive green or red candles
    2. Find matching row in table above
    3. Look at "Polymarket Bet" column
    4. Check "Quality" - only bet on A+ or A
    5. Go to Polymarket → Find "Will next 15m BTC candle be BULLISH?"
    6. Place your bet (YES or NO as indicated)

    Example:
    - You see 4 consecutive green candles
    - Table says: Predict BEARISH, Bet NO, Quality: A
    - Action: Bet NO on "Will next 15m BTC candle be BULLISH?"
    - Expected edge: Check table for percentage
    """)


if __name__ == "__main__":
    # Run full demo
    demo_predictions()
    create_signal_table()
    real_time_example()
