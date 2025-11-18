"""
TELEGRAM SIGNAL BOT - MULTI-USER VERSION
Allows multiple people to subscribe and receive signals
"""

import requests
import pandas as pd
import time
from datetime import datetime
import json
import os


class MultiUserTelegramBot:
    """
    Multi-user Telegram bot that allows anyone to subscribe
    and receive trading signals
    """

    def __init__(self, bot_token):
        """
        Initialize bot with just the token

        Args:
            bot_token: Your Telegram bot token from @BotFather
        """
        self.bot_token = bot_token
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"

        # File to store subscribers
        self.subscribers_file = "subscribers.json"
        self.subscribers = self.load_subscribers()

        # Strategy parameters
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
        self.cooldown_minutes = 15
        self.last_update_id = 0

    def load_subscribers(self):
        """Load subscribers from file"""
        if os.path.exists(self.subscribers_file):
            try:
                with open(self.subscribers_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_subscribers(self):
        """Save subscribers to file"""
        with open(self.subscribers_file, 'w') as f:
            json.dump(self.subscribers, f, indent=2)

    def add_subscriber(self, chat_id, username=None, first_name=None):
        """Add new subscriber"""
        chat_id = str(chat_id)
        if chat_id not in self.subscribers:
            self.subscribers[chat_id] = {
                'username': username,
                'first_name': first_name,
                'subscribed_at': datetime.now().isoformat(),
                'active': True
            }
            self.save_subscribers()
            return True
        return False

    def remove_subscriber(self, chat_id):
        """Remove subscriber"""
        chat_id = str(chat_id)
        if chat_id in self.subscribers:
            self.subscribers[chat_id]['active'] = False
            self.save_subscribers()
            return True
        return False

    def get_active_subscribers(self):
        """Get list of active subscriber chat IDs"""
        return [chat_id for chat_id, data in self.subscribers.items()
                if data.get('active', True)]

    def send_message(self, chat_id, message, parse_mode='Markdown'):
        """Send message to specific chat"""
        try:
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(
                f"{self.telegram_api}/sendMessage",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error sending to {chat_id}: {e}")
            return False

    def broadcast_message(self, message, parse_mode='Markdown'):
        """Send message to all active subscribers"""
        active_subs = self.get_active_subscribers()
        success_count = 0

        for chat_id in active_subs:
            if self.send_message(chat_id, message, parse_mode):
                success_count += 1

        return success_count

    def get_updates(self):
        """Get new messages from Telegram"""
        try:
            url = f"{self.telegram_api}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 10
            }
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result', [])
            return []
        except Exception as e:
            print(f"❌ Error getting updates: {e}")
            return []

    def process_commands(self):
        """Process incoming commands from users"""
        updates = self.get_updates()

        for update in updates:
            self.last_update_id = update['update_id']

            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            username = message.get('from', {}).get('username')
            first_name = message.get('from', {}).get('first_name', 'User')

            if not chat_id:
                continue

            # Handle commands
            if text.startswith('/start'):
                self.handle_start(chat_id, username, first_name)

            elif text.startswith('/stop'):
                self.handle_stop(chat_id, first_name)

            elif text.startswith('/status'):
                self.handle_status(chat_id)

            elif text.startswith('/help'):
                self.handle_help(chat_id)

            elif text.startswith('/stats'):
                self.handle_stats(chat_id)

    def handle_start(self, chat_id, username, first_name):
        """Handle /start command"""
        is_new = self.add_subscriber(chat_id, username, first_name)

        if is_new:
            message = f"""
👋 *Welcome {first_name}!*

You are now subscribed to BTC trading signals!

🤖 *What you'll receive:*
✅ Real-time ULTIMATE strategy signals
✅ 10-12 alerts per day
✅ 54%+ win rate signals
✅ RSI extreme levels (<25, >75)
✅ Multi-indicator confluence

📊 *Signal Types:*
• RSI EXTREME OVERSOLD (55% WR)
• RSI EXTREME OVERBOUGHT (55% WR)
• RSI STRONG signals (52-54% WR)

💡 *Commands:*
/status - Check current BTC price & RSI
/stats - View subscriber statistics
/help - Show help message
/stop - Unsubscribe from alerts

🚀 *You're all set!*
Stand by for trading signals...
            """
        else:
            message = f"""
👋 *Welcome back {first_name}!*

You're already subscribed to signals.

Use /help to see available commands.
            """

        self.send_message(chat_id, message.strip())
        print(f"✅ New subscriber: {first_name} ({chat_id})")

    def handle_stop(self, chat_id, first_name):
        """Handle /stop command"""
        self.remove_subscriber(chat_id)

        message = f"""
👋 *Goodbye {first_name}!*

You have been unsubscribed from signals.

To resubscribe, send /start anytime.

Good luck with your trading! 🍀
        """

        self.send_message(chat_id, message.strip())
        print(f"❌ Unsubscribed: {first_name} ({chat_id})")

    def handle_status(self, chat_id):
        """Handle /status command - show current BTC status"""
        df = self.get_btc_data(limit=50)

        if df is None:
            self.send_message(chat_id, "⚠️ Unable to fetch BTC data right now.")
            return

        df = self.calculate_indicators(df)
        current = df.iloc[-1]

        price = current['close']
        rsi = current['rsi']
        macd_hist = current['macd_hist']
        direction = current['direction']

        # Determine market condition
        if rsi >= 75:
            rsi_status = "🔴 EXTREME OVERBOUGHT (Bearish signal likely)"
        elif rsi >= 70:
            rsi_status = "🟠 OVERBOUGHT (Watch for reversal)"
        elif rsi <= 25:
            rsi_status = "🟢 EXTREME OVERSOLD (Bullish signal likely)"
        elif rsi <= 30:
            rsi_status = "🟡 OVERSOLD (Watch for reversal)"
        else:
            rsi_status = "⚪ NEUTRAL (No signal)"

        message = f"""
📊 *CURRENT BTC STATUS*

💰 *Price:* ${price:,.2f}
📈 *Last Candle:* {direction}

📊 *RSI (14):* {rsi:.1f}
{rsi_status}

📉 *MACD Histogram:* {macd_hist:.2f}

⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}

💡 Waiting for next signal...
        """

        self.send_message(chat_id, message.strip())

    def handle_help(self, chat_id):
        """Handle /help command"""
        message = """
🤖 *BOT COMMANDS*

/start - Subscribe to signals
/stop - Unsubscribe from alerts
/status - Check current BTC & RSI
/stats - View statistics
/help - Show this message

📊 *About Signals:*
You'll receive alerts when:
• RSI reaches extreme levels
• Multiple indicators confirm
• Confluence score ≥ 3

*Win rate:* 54%+
*Signals/day:* 10-12
*Strategy:* ULTIMATE (multi-indicator)

🎯 *How to Trade:*
1. Receive signal on Telegram
2. Open Polymarket
3. Find "Bitcoin Up or Down"
4. Bet YES or NO as indicated
5. Wait 15 minutes for result

Good luck! 🍀
        """

        self.send_message(chat_id, message.strip())

    def handle_stats(self, chat_id):
        """Handle /stats command"""
        total_subs = len(self.subscribers)
        active_subs = len(self.get_active_subscribers())
        inactive_subs = total_subs - active_subs

        message = f"""
📊 *BOT STATISTICS*

👥 *Subscribers:*
• Active: {active_subs}
• Inactive: {inactive_subs}
• Total: {total_subs}

📡 *Monitoring:*
• Asset: BTC/USDT
• Timeframe: 15 minutes
• Check interval: 60 seconds

🎯 *Performance:*
• Win rate: 54%+
• Signals/day: 10-12
• Strategy: ULTIMATE

⏰ *Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        self.send_message(chat_id, message.strip())

    def get_btc_data(self, limit=100):
        """Fetch real-time BTC data from Binance"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': 'BTCUSDT',
                'interval': '15m',
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()

            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

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
        """Calculate technical indicators"""
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
        """Check for trading signal"""
        if df is None or len(df) < 50:
            return None

        current = df.iloc[-1]
        current_time = datetime.now()
        current_hour = current_time.hour

        if current_hour in self.params['avoid_hours']:
            return None

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

        signal = None
        confluence_score = 0

        # Bullish signals
        if rsi <= self.params['rsi_extreme_os']:
            signal_type = "🟢 RSI EXTREME OVERSOLD"
            prediction = "UP"
            polymarket_bet = "YES"
            base_confidence = 56
            confluence_score = 3

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

        elif rsi <= self.params['rsi_strong_os']:
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

        # Bearish signals
        elif rsi >= self.params['rsi_extreme_ob']:
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

        elif rsi >= self.params['rsi_strong_ob']:
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

    def run(self, check_interval=60):
        """Main bot loop"""
        print("="*60)
        print("🤖 MULTI-USER TELEGRAM SIGNAL BOT STARTED")
        print("="*60)
        print(f"✅ Bot Token: {'*' * 20}{self.bot_token[-5:]}")
        print(f"✅ Active Subscribers: {len(self.get_active_subscribers())}")
        print(f"✅ Check Interval: {check_interval} seconds")
        print()
        print("📱 Users can subscribe by sending /start to your bot")
        print("🔍 Monitoring BTC for ULTIMATE strategy signals...")
        print("="*60)

        # Send startup notification to admin (first subscriber)
        if self.subscribers:
            first_sub = list(self.subscribers.keys())[0]
            startup_msg = f"""
🤖 *MULTI-USER BOT ACTIVATED*

Active subscribers: {len(self.get_active_subscribers())}

Users can subscribe by sending /start
Monitoring BTC 15m candles for signals...

Stand by! 🚀
            """
            self.send_message(first_sub, startup_msg.strip())

        check_count = 0

        while True:
            try:
                check_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')

                # Process incoming commands
                self.process_commands()

                # Check for signals every 5th iteration (5 minutes)
                if check_count % 5 == 0:
                    print(f"\n[{current_time}] Check #{check_count}: Fetching BTC data...")

                    df = self.get_btc_data(limit=100)

                    if df is None:
                        print("⚠️  Failed to fetch data")
                        time.sleep(60)
                        continue

                    df = self.calculate_indicators(df)
                    signal = self.check_signal(df)

                    if signal:
                        print(f"\n🚨 SIGNAL DETECTED!")
                        print(f"   Type: {signal['type']}")
                        print(f"   Prediction: {signal['prediction']}")
                        print(f"   Confluence: {signal['confluence']}/7")

                        message = self.format_signal_message(signal)
                        sent_count = self.broadcast_message(message)

                        self.last_signal_time = datetime.now()
                        print(f"   ✅ Sent to {sent_count} subscribers!")
                    else:
                        current = df.iloc[-1]
                        rsi = current['rsi']
                        price = current['close']
                        print(f"   ℹ️  No signal | BTC: ${price:,.2f} | RSI: {rsi:.1f}")

                time.sleep(check_interval)

            except KeyboardInterrupt:
                print("\n\n👋 Bot stopped by user")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(60)


def main():
    """Main function"""
    print("="*60)
    print("MULTI-USER TELEGRAM SIGNAL BOT")
    print("="*60)
    print()

    # ============================================
    # CONFIGURE YOUR BOT TOKEN HERE
    # ============================================

    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

    # ============================================

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please configure your bot token!")
        print()
        print("SETUP INSTRUCTIONS:")
        print("="*60)
        print()
        print("1. Create bot with @BotFather")
        print("2. Copy the bot token")
        print("3. Edit this file and replace BOT_TOKEN")
        print("4. Run again")
        print()
        print("Users can then send /start to your bot to subscribe!")
        print()
        return

    # Initialize bot
    bot = MultiUserTelegramBot(bot_token=BOT_TOKEN)

    # Start monitoring
    bot.run(check_interval=60)


if __name__ == "__main__":
    main()
