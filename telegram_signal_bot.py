"""
TELEGRAM SIGNAL BOT FOR ULTIMATE STRATEGY
Sends real-time trading signals to your Telegram when entry conditions are met
"""

import requests
import pandas as pd
import time
from datetime import datetime
import json


class TelegramSignalBot:
    """
    Real-time signal bot that monitors BTC and sends Telegram alerts
    when ULTIMATE strategy entry conditions are met
    """

    def __init__(self, bot_token, chat_id):
        """
        Initialize Telegram bot

        Args:
            bot_token: Your Telegram bot token from @BotFather
            chat_id: Your Telegram chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Strategy parameters (from ULTIMATE strategy)
        self.params = {
            'rsi_period': 14,
            'rsi_extreme_ob': 75,
            'rsi_extreme_os': 25,
            'rsi_strong_ob': 70,
            'rsi_strong_os': 30,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'ema_fast': 9,
            'ema_slow': 21,
            'avoid_hours': [0, 1, 2, 3, 4, 5],
            'best_hours': [9, 10, 11, 14, 15, 16, 17, 20, 21, 22],
        }

        self.last_signal_time = None
        self.cooldown_minutes = 15  # Don't spam same signal

    def send_telegram_message(self, message, parse_mode='Markdown'):
        """Send message to Telegram"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(self.telegram_api, json=payload, timeout=10)

            if response.status_code == 200:
                print(f"✅ Signal sent to Telegram!")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False

    def get_btc_data(self, limit=100):
        """Fetch real-time BTC 15-minute data from Binance"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': 'BTCUSDT',
                'interval': '15m',
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"❌ Binance API error: {response.status_code}")
                return None

            data = response.json()

            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert to proper types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)

            return df

        except Exception as e:
            print(f"❌ Error fetching BTC data: {e}")
            return None

    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.params['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['close'].ewm(span=self.params['macd_fast']).mean()
        exp2 = df['close'].ewm(span=self.params['macd_slow']).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.params['macd_signal']).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # EMAs
        df['ema_fast'] = df['close'].ewm(span=self.params['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=self.params['ema_slow']).mean()

        # Momentum
        df['momentum'] = df['close'].diff(10)

        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Direction
        df['direction'] = df.apply(
            lambda r: "UP" if r['close'] > r['open'] else "DOWN",
            axis=1
        )

        return df

    def check_signal(self, df):
        """Check for ULTIMATE strategy signal"""
        if df is None or len(df) < 50:
            return None

        current = df.iloc[-1]
        current_time = datetime.now()
        current_hour = current_time.hour

        # Skip if in avoid hours
        if current_hour in self.params['avoid_hours']:
            return None

        # Cooldown check
        if self.last_signal_time:
            time_diff = (current_time - self.last_signal_time).total_seconds() / 60
            if time_diff < self.cooldown_minutes:
                return None

        rsi = current['rsi']
        macd_hist = current['macd_hist']
        ema_diff = current['ema_fast'] - current['ema_slow']
        momentum = current['momentum']
        volume_ratio = current['volume_ratio']
        price = current['close']

        # Check for signals
        signal = None
        confluence_score = 0

        # === BULLISH SIGNALS ===
        if rsi <= self.params['rsi_extreme_os']:  # RSI < 25
            signal_type = "🟢 RSI EXTREME OVERSOLD"
            prediction = "UP"
            polymarket_bet = "YES"
            base_confidence = 56
            confluence_score = 3

            # Add confluence
            if macd_hist > 0:
                confluence_score += 1
            if momentum < 0:
                confluence_score += 1
            if ema_diff < 0:
                confluence_score += 1
            if volume_ratio > 1.5:
                confluence_score += 1
            if current_hour in self.params['best_hours']:
                confluence_score += 1

            if confluence_score >= 3:
                signal = {
                    'type': signal_type,
                    'prediction': prediction,
                    'polymarket_bet': polymarket_bet,
                    'confidence': base_confidence + (confluence_score - 3),
                    'confluence': confluence_score,
                    'rsi': rsi,
                    'price': price,
                    'macd_hist': macd_hist,
                    'volume_ratio': volume_ratio
                }

        elif rsi <= self.params['rsi_strong_os']:  # RSI < 30
            signal_type = "🟢 RSI STRONG OVERSOLD"
            prediction = "UP"
            polymarket_bet = "YES"
            base_confidence = 54
            confluence_score = 2

            if macd_hist > 0:
                confluence_score += 1
            if momentum < 0:
                confluence_score += 1
            if current_hour in self.params['best_hours']:
                confluence_score += 1

            if confluence_score >= 3:
                signal = {
                    'type': signal_type,
                    'prediction': prediction,
                    'polymarket_bet': polymarket_bet,
                    'confidence': base_confidence + (confluence_score - 3),
                    'confluence': confluence_score,
                    'rsi': rsi,
                    'price': price,
                    'macd_hist': macd_hist,
                    'volume_ratio': volume_ratio
                }

        # === BEARISH SIGNALS ===
        elif rsi >= self.params['rsi_extreme_ob']:  # RSI > 75
            signal_type = "🔴 RSI EXTREME OVERBOUGHT"
            prediction = "DOWN"
            polymarket_bet = "NO"
            base_confidence = 56
            confluence_score = 3

            if macd_hist < 0:
                confluence_score += 1
            if momentum > 0:
                confluence_score += 1
            if ema_diff > 0:
                confluence_score += 1
            if volume_ratio > 1.5:
                confluence_score += 1
            if current_hour in self.params['best_hours']:
                confluence_score += 1

            if confluence_score >= 3:
                signal = {
                    'type': signal_type,
                    'prediction': prediction,
                    'polymarket_bet': polymarket_bet,
                    'confidence': base_confidence + (confluence_score - 3),
                    'confluence': confluence_score,
                    'rsi': rsi,
                    'price': price,
                    'macd_hist': macd_hist,
                    'volume_ratio': volume_ratio
                }

        elif rsi >= self.params['rsi_strong_ob']:  # RSI > 70
            signal_type = "🔴 RSI STRONG OVERBOUGHT"
            prediction = "DOWN"
            polymarket_bet = "NO"
            base_confidence = 54
            confluence_score = 2

            if macd_hist < 0:
                confluence_score += 1
            if momentum > 0:
                confluence_score += 1
            if current_hour in self.params['best_hours']:
                confluence_score += 1

            if confluence_score >= 3:
                signal = {
                    'type': signal_type,
                    'prediction': prediction,
                    'polymarket_bet': polymarket_bet,
                    'confidence': base_confidence + (confluence_score - 3),
                    'confluence': confluence_score,
                    'rsi': rsi,
                    'price': price,
                    'macd_hist': macd_hist,
                    'volume_ratio': volume_ratio
                }

        return signal

    def format_signal_message(self, signal):
        """Format signal as Telegram message"""

        # Emoji based on prediction
        direction_emoji = "📈" if signal['prediction'] == "UP" else "📉"

        message = f"""
🚨 *POLYMARKET BTC SIGNAL ALERT* 🚨

{signal['type']}

━━━━━━━━━━━━━━━━━━━━━
📊 *SIGNAL DETAILS*

{direction_emoji} *Prediction:* {signal['prediction']}
🎯 *Polymarket Bet:* *{signal['polymarket_bet']}*
💯 *Confidence:* {signal['confidence']}%
⭐ *Confluence Score:* {signal['confluence']}/7

━━━━━━━━━━━━━━━━━━━━━
📈 *MARKET DATA*

💰 *BTC Price:* ${signal['price']:,.2f}
📊 *RSI:* {signal['rsi']:.1f}
📉 *MACD Hist:* {signal['macd_hist']:.2f}
📦 *Volume:* {signal['volume_ratio']:.1f}x

━━━━━━━━━━━━━━━━━━━━━
💡 *ACTION REQUIRED*

1️⃣ Open Polymarket
2️⃣ Find "Bitcoin Up or Down" market
3️⃣ Bet *{signal['polymarket_bet']}* (predict next candle {signal['prediction']})
4️⃣ Position size: 10% of capital
5️⃣ Wait 15 minutes for result

━━━━━━━━━━━━━━━━━━━━━
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*Good luck!* 🍀
        """

        return message.strip()

    def monitor_and_signal(self, check_interval=60):
        """
        Monitor BTC price and send signals

        Args:
            check_interval: Seconds between checks (default 60)
        """
        print("="*60)
        print("🤖 TELEGRAM SIGNAL BOT STARTED")
        print("="*60)
        print(f"✅ Bot Token: {'*' * 20}{self.bot_token[-5:]}")
        print(f"✅ Chat ID: {self.chat_id}")
        print(f"✅ Check Interval: {check_interval} seconds")
        print(f"✅ Cooldown: {self.cooldown_minutes} minutes")
        print()
        print("🔍 Monitoring BTC for ULTIMATE strategy signals...")
        print("=" * 60)

        # Send startup message
        startup_msg = """
🤖 *TELEGRAM SIGNAL BOT ACTIVATED*

Your ULTIMATE Strategy signal bot is now monitoring BTC 15-minute candles.

You will receive alerts when:
✅ RSI reaches extreme levels (<25 or >75)
✅ Multiple indicators confirm (confluence ≥3)
✅ High-probability setup detected

*Expected signals:* 10-12 per day
*Win rate:* 54%+

Stand by for signals... 🚀
        """
        self.send_telegram_message(startup_msg)

        check_count = 0

        while True:
            try:
                check_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')

                print(f"\n[{current_time}] Check #{check_count}: Fetching BTC data...")

                # Get data
                df = self.get_btc_data(limit=100)

                if df is None:
                    print("⚠️  Failed to fetch data, retrying in 60s...")
                    time.sleep(60)
                    continue

                # Calculate indicators
                df = self.calculate_indicators(df)

                # Check for signal
                signal = self.check_signal(df)

                if signal:
                    print(f"\n🚨 SIGNAL DETECTED!")
                    print(f"   Type: {signal['type']}")
                    print(f"   Prediction: {signal['prediction']}")
                    print(f"   Bet: {signal['polymarket_bet']}")
                    print(f"   Confidence: {signal['confidence']}%")
                    print(f"   Confluence: {signal['confluence']}/7")

                    # Format and send
                    message = self.format_signal_message(signal)
                    success = self.send_telegram_message(message)

                    if success:
                        self.last_signal_time = datetime.now()
                        print(f"   ✅ Alert sent to Telegram!")
                    else:
                        print(f"   ❌ Failed to send alert")
                else:
                    # No signal, show current status
                    current = df.iloc[-1]
                    rsi = current['rsi']
                    price = current['close']
                    print(f"   ℹ️  No signal | BTC: ${price:,.2f} | RSI: {rsi:.1f}")

                # Wait before next check
                print(f"   ⏳ Next check in {check_interval} seconds...")
                time.sleep(check_interval)

            except KeyboardInterrupt:
                print("\n\n👋 Bot stopped by user")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")
                print(f"   Retrying in 60 seconds...")
                time.sleep(60)


def main():
    """
    Main function - Set your Telegram credentials here
    """

    print("="*60)
    print("TELEGRAM SIGNAL BOT SETUP")
    print("="*60)
    print()
    print("To use this bot, you need:")
    print("1. Telegram Bot Token (from @BotFather)")
    print("2. Your Telegram Chat ID (from @userinfobot)")
    print()
    print("="*60)
    print()

    # ============================================
    # CONFIGURE YOUR TELEGRAM CREDENTIALS HERE
    # ============================================

    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
    CHAT_ID = "YOUR_CHAT_ID_HERE"      # Get from @userinfobot

    # ============================================

    # Validate credentials
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ ERROR: Please configure your Telegram credentials!")
        print()
        print("SETUP INSTRUCTIONS:")
        print("="*60)
        print()
        print("Step 1: Create Telegram Bot")
        print("   1. Open Telegram and search for @BotFather")
        print("   2. Send /newbot")
        print("   3. Follow instructions to create bot")
        print("   4. Copy the bot token")
        print()
        print("Step 2: Get Your Chat ID")
        print("   1. Search for @userinfobot in Telegram")
        print("   2. Start the bot")
        print("   3. It will show your Chat ID")
        print("   4. Copy the Chat ID")
        print()
        print("Step 3: Configure This Script")
        print("   1. Open telegram_signal_bot.py in a text editor")
        print("   2. Find the lines:")
        print("      BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'")
        print("      CHAT_ID = 'YOUR_CHAT_ID_HERE'")
        print("   3. Replace with your actual credentials")
        print("   4. Save and run again")
        print()
        print("="*60)
        return

    # Initialize bot
    bot = TelegramSignalBot(
        bot_token=BOT_TOKEN,
        chat_id=CHAT_ID
    )

    # Start monitoring
    # Check every 60 seconds (1 minute)
    bot.monitor_and_signal(check_interval=60)


if __name__ == "__main__":
    main()
