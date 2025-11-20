"""
TELEGRAM SIGNAL BOT WITH RESULT TRACKING
Automatically verifies signals and shows win/loss tracking
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import os
import threading


class SignalTrackingBot:
    """
    Enhanced bot that tracks signal results and shows performance
    """

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"

        # Files
        self.subscribers_file = "subscribers.json"
        self.signals_file = "signals_history.json"

        self.subscribers = self.load_subscribers()
        self.signals_history = self.load_signals_history()

        # Daily stats
        self.daily_stats = {
            'date': datetime.now().date().isoformat(),
            'total_signals': 0,
            'wins': 0,
            'losses': 0,
            'pending': 0
        }

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
        """Load subscribers"""
        if os.path.exists(self.subscribers_file):
            try:
                with open(self.subscribers_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_subscribers(self):
        """Save subscribers"""
        with open(self.subscribers_file, 'w') as f:
            json.dump(self.subscribers, f, indent=2)

    def load_signals_history(self):
        """Load signals history"""
        if os.path.exists(self.signals_file):
            try:
                with open(self.signals_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_signals_history(self):
        """Save signals history"""
        with open(self.signals_file, 'w') as f:
            json.dump(self.signals_history, f, indent=2)

    def add_subscriber(self, chat_id, username=None, first_name=None):
        """Add subscriber"""
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
        """Get active subscribers"""
        return [chat_id for chat_id, data in self.subscribers.items()
                if data.get('active', True)]

    def send_message(self, chat_id, message, parse_mode='Markdown'):
        """Send message"""
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
        """Broadcast to all subscribers"""
        active_subs = self.get_active_subscribers()
        success_count = 0

        for chat_id in active_subs:
            if self.send_message(chat_id, message, parse_mode):
                success_count += 1

        return success_count

    def get_updates(self):
        """Get Telegram updates"""
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
        """Process commands"""
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

            if text.startswith('/start'):
                self.handle_start(chat_id, username, first_name)
            elif text.startswith('/stop'):
                self.handle_stop(chat_id, first_name)
            elif text.startswith('/status'):
                self.handle_status(chat_id)
            elif text.startswith('/stats'):
                self.handle_stats(chat_id)
            elif text.startswith('/today'):
                self.handle_today(chat_id)
            elif text.startswith('/help'):
                self.handle_help(chat_id)

    def handle_start(self, chat_id, username, first_name):
        """Handle /start"""
        is_new = self.add_subscriber(chat_id, username, first_name)

        message = f"""
👋 *Welcome {first_name}!*

You are now subscribed to BTC signals with *automatic result tracking*!

🎯 *What you'll receive:*
✅ Real-time signals (10-12/day)
✅ *Automatic result verification* (after 15 min)
✅ Win/Loss tracking for each signal
✅ Daily performance stats

📊 *Commands:*
/today - Today's performance
/status - Current BTC & RSI
/stats - Bot statistics
/help - Show help
/stop - Unsubscribe

🚀 Stand by for signals!
        """

        self.send_message(chat_id, message.strip())
        print(f"✅ Subscriber: {first_name} ({chat_id})")

    def handle_stop(self, chat_id, first_name):
        """Handle /stop"""
        self.remove_subscriber(chat_id)
        message = f"👋 Goodbye {first_name}! Unsubscribed. Send /start to rejoin."
        self.send_message(chat_id, message)

    def handle_status(self, chat_id):
        """Handle /status"""
        df = self.get_btc_data(limit=50)
        if df is None:
            self.send_message(chat_id, "⚠️ Unable to fetch data")
            return

        df = self.calculate_indicators(df)
        current = df.iloc[-1]

        message = f"""
📊 *CURRENT BTC STATUS*

💰 *Price:* ${current['close']:,.2f}
📈 *Last Candle:* {current['direction']}
📊 *RSI:* {current['rsi']:.1f}
📉 *MACD:* {current['macd_hist']:.2f}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(chat_id, message.strip())

    def handle_stats(self, chat_id):
        """Handle /stats"""
        total = len(self.signals_history)
        if total == 0:
            self.send_message(chat_id, "📊 No signals sent yet.")
            return

        verified = [s for s in self.signals_history if s.get('result') is not None]
        wins = [s for s in verified if s.get('result') == 'WIN']
        losses = [s for s in verified if s.get('result') == 'LOSS']

        wr = (len(wins) / len(verified) * 100) if verified else 0

        message = f"""
📊 *ALL-TIME STATISTICS*

📡 *Total Signals:* {total}
✅ *Wins:* {len(wins)}
❌ *Losses:* {len(losses)}
📊 *Win Rate:* {wr:.1f}%

👥 *Subscribers:* {len(self.get_active_subscribers())}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        self.send_message(chat_id, message.strip())

    def handle_today(self, chat_id):
        """Handle /today - show today's performance"""
        today = datetime.now().date().isoformat()
        today_signals = [s for s in self.signals_history
                        if s.get('date') == today]

        if not today_signals:
            self.send_message(chat_id, "📊 No signals today yet.")
            return

        total = len(today_signals)
        wins = [s for s in today_signals if s.get('result') == 'WIN']
        losses = [s for s in today_signals if s.get('result') == 'LOSS']
        pending = [s for s in today_signals if s.get('result') is None]

        wr = (len(wins) / (len(wins) + len(losses)) * 100) if (wins or losses) else 0

        message = f"""
📅 *TODAY'S PERFORMANCE*

🎯 *Total Signals:* {total}
✅ *Wins:* {len(wins)}
❌ *Losses:* {len(losses)}
⏳ *Pending:* {len(pending)}
📊 *Win Rate:* {wr:.1f}%

⏰ Updated: {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(chat_id, message.strip())

    def handle_help(self, chat_id):
        """Handle /help"""
        message = """
🤖 *BOT COMMANDS*

/start - Subscribe to signals
/today - Today's win/loss record
/status - Current BTC & RSI
/stats - All-time statistics
/help - This message
/stop - Unsubscribe

🎯 *Features:*
• Real-time signals
• Automatic result tracking
• Win/Loss verification
• Daily performance stats

Good luck! 🍀
        """
        self.send_message(chat_id, message.strip())

    def get_btc_data(self, limit=100):
        """Get BTC data"""
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
            print(f"❌ Error: {e}")
            return None

    def calculate_indicators(self, df):
        """Calculate indicators"""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.params['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        exp1 = df['close'].ewm(span=self.params['macd_fast']).mean()
        exp2 = df['close'].ewm(span=self.params['macd_slow']).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.params['macd_signal']).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        df['ema_fast'] = df['close'].ewm(span=self.params['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=self.params['ema_slow']).mean()
        df['momentum'] = df['close'].diff(10)
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        df['direction'] = df.apply(
            lambda r: "UP" if r['close'] > r['open'] else "DOWN",
            axis=1
        )

        return df

    def check_signal(self, df):
        """Check for signal"""
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

        # Check signals (same logic as before)
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

    def get_next_candle_times(self):
        """Calculate next 15-min candle boundaries"""
        now = datetime.now()

        # Round down to nearest 15-min
        current_minute = (now.minute // 15) * 15
        current_candle_start = now.replace(minute=current_minute, second=0, microsecond=0)
        current_candle_close = current_candle_start + timedelta(minutes=15)

        # Next candle times
        next_candle_open = current_candle_close
        next_candle_close = next_candle_open + timedelta(minutes=15)

        # Time until current candle closes
        seconds_until_close = (current_candle_close - now).total_seconds()

        return {
            'current_candle_start': current_candle_start,
            'current_candle_close': current_candle_close,
            'next_candle_open': next_candle_open,
            'next_candle_close': next_candle_close,
            'seconds_until_close': seconds_until_close,
            'minutes_until_close': int(seconds_until_close / 60)
        }

    def format_signal_message(self, signal, signal_number, candle_info):
        """Format signal message with candle timing"""
        direction_emoji = "📈" if signal['prediction'] == "UP" else "📉"

        # Determine which candle to trade
        time_left = candle_info['minutes_until_close']

        if time_left >= 10:
            # Enough time - trade CURRENT candle
            trade_candle = "CURRENT"
            candle_open = candle_info['current_candle_start'].strftime('%H:%M')
            candle_close = candle_info['current_candle_close'].strftime('%H:%M')
            entry_window = f"Enter NOW (you have {time_left} min)"
            target_candle_close = candle_info['current_candle_close']
        else:
            # Not enough time - trade NEXT candle
            trade_candle = "NEXT"
            candle_open = candle_info['next_candle_open'].strftime('%H:%M')
            candle_close = candle_info['next_candle_close'].strftime('%H:%M')
            entry_window = f"Wait & enter at {candle_open}"
            target_candle_close = candle_info['next_candle_close']

        signal['target_candle_close'] = target_candle_close.isoformat()
        signal['trade_candle'] = trade_candle

        message = f"""
🚨 *SIGNAL #{signal_number}* 🚨

{signal['type']}

━━━━━━━━━━━━━━━━━━━━━
📊 *SIGNAL DETAILS*

{direction_emoji} *Prediction:* {signal['prediction']}
🎯 *Polymarket Bet:* *{signal['polymarket_bet']}*
💯 *Confidence:* {signal['confidence']}%
⭐ *Confluence:* {signal['confluence']}/7

━━━━━━━━━━━━━━━━━━━━━
⏰ *CANDLE TIMING* ⏰

🕐 *Trade {trade_candle} Candle*
📅 Opens: {candle_open}
📅 Closes: {candle_close}

💡 *ENTRY:* {entry_window}

━━━━━━━━━━━━━━━━━━━━━
📈 *MARKET DATA*

💰 *BTC Price:* ${signal['price']:,.2f}
📊 *RSI:* {signal['rsi']:.1f}
📉 *MACD:* {signal['macd_hist']:.2f}
📦 *Volume:* {signal['volume_ratio']:.1f}x

━━━━━━━━━━━━━━━━━━━━━
💡 *ACTION*

Bet *{signal['polymarket_bet']}* (predict {signal['prediction']})
On the *{candle_open} - {candle_close}* candle

⏰ *Sent:* {datetime.now().strftime('%H:%M:%S')}

📊 *Today so far:* {self.daily_stats['total_signals']} signals, {self.daily_stats['wins']} wins, {self.daily_stats['losses']} losses
        """

        return message.strip()

    def verify_signal_result(self, signal_data):
        """Verify signal result at exact candle close time"""
        # Calculate wait time until target candle closes
        target_close_time = datetime.fromisoformat(signal_data['target_candle_close'])
        now = datetime.now()
        wait_seconds = (target_close_time - now).total_seconds()

        # Add buffer to ensure candle data is available
        wait_seconds += 60  # Wait 1 min after candle close

        if wait_seconds > 0:
            print(f"   ⏳ Waiting {int(wait_seconds/60)} minutes until candle closes...")
            time.sleep(wait_seconds)

        print(f"\n⏰ Verifying signal result...")

        # Get new data
        df = self.get_btc_data(limit=50)
        if df is None:
            print("❌ Could not verify (no data)")
            return

        # Calculate indicators (CRITICAL - adds 'direction' column)
        df = self.calculate_indicators(df)

        # Find the candle that matches our target close time
        # The candle we want is the one that closed at target_close_time
        # In Binance data, this is the candle with close_time matching our target
        target_timestamp = int(target_close_time.timestamp() * 1000)

        # Get the candle closest to our target time
        # Usually it's the last completed candle (iloc[-2]) if we just closed
        # or iloc[-1] if some time has passed
        verified_candle = df.iloc[-2]  # Last COMPLETED candle

        actual_direction = verified_candle['direction']
        actual_price = verified_candle['close']

        # Compare
        predicted = signal_data['prediction']
        result = "WIN" if predicted == actual_direction else "LOSS"

        # Update signal data
        signal_data['result'] = result
        signal_data['actual_direction'] = actual_direction
        signal_data['actual_price'] = float(actual_price)
        signal_data['verified_at'] = datetime.now().isoformat()

        # Save
        self.save_signals_history()

        # Update daily stats
        if result == "WIN":
            self.daily_stats['wins'] += 1
        else:
            self.daily_stats['losses'] += 1
        self.daily_stats['pending'] -= 1

        # Calculate today's stats
        today_signals = self.daily_stats['total_signals']
        today_wins = self.daily_stats['wins']
        today_losses = self.daily_stats['losses']
        today_wr = (today_wins / (today_wins + today_losses) * 100) if (today_wins + today_losses) > 0 else 0

        # Format result message
        if result == "WIN":
            result_emoji = "✅"
            result_text = "WIN!"
        else:
            result_emoji = "❌"
            result_text = "LOSS"

        # Get candle time info
        candle_close_time = target_close_time.strftime('%H:%M')

        result_message = f"""
{result_emoji} *SIGNAL #{signal_data['number']} RESULT* {result_emoji}

━━━━━━━━━━━━━━━━━━━━━
📊 *VERIFICATION*

🕐 *Candle Closed:* {candle_close_time}
💰 *Close Price:* ${actual_price:,.2f}

🎯 *Predicted:* {predicted}
📈 *Actual:* {actual_direction}
🏆 *Result:* *{result_text}*

━━━━━━━━━━━━━━━━━━━━━
📅 *TODAY'S SCORE*

🎯 Total: {today_signals} signals
✅ Wins: {today_wins}
❌ Losses: {today_losses}
📊 Win Rate: {today_wr:.1f}%

━━━━━━━━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%H:%M:%S')}
        """

        # Send to all subscribers
        sent = self.broadcast_message(result_message.strip())
        print(f"✅ Result sent to {sent} subscribers: {result}")

    def run(self, check_interval=60):
        """Main loop"""
        print("="*60)
        print("🤖 SIGNAL TRACKING BOT STARTED")
        print("="*60)
        print(f"✅ Subscribers: {len(self.get_active_subscribers())}")
        print(f"✅ Auto result verification enabled!")
        print()
        print("🔍 Monitoring BTC...")
        print("="*60)

        check_count = 0

        while True:
            try:
                check_count += 1
                current_time = datetime.now()

                # Reset daily stats if new day
                if current_time.date().isoformat() != self.daily_stats['date']:
                    self.daily_stats = {
                        'date': current_time.date().isoformat(),
                        'total_signals': 0,
                        'wins': 0,
                        'losses': 0,
                        'pending': 0
                    }

                # Process commands
                self.process_commands()

                # Check for signals every 5th iteration
                if check_count % 5 == 0:
                    print(f"\n[{current_time.strftime('%H:%M:%S')}] Checking for signal...")

                    df = self.get_btc_data(limit=100)
                    if df is None:
                        print("⚠️  No data")
                        time.sleep(60)
                        continue

                    df = self.calculate_indicators(df)
                    signal = self.check_signal(df)

                    if signal:
                        # Increment signal counter
                        self.daily_stats['total_signals'] += 1
                        self.daily_stats['pending'] += 1
                        signal_number = self.daily_stats['total_signals']

                        # Calculate candle timing
                        candle_info = self.get_next_candle_times()

                        print(f"\n🚨 SIGNAL #{signal_number} DETECTED!")
                        print(f"   Type: {signal['type']}")
                        print(f"   Prediction: {signal['prediction']}")

                        # Send signal with candle timing info
                        message = self.format_signal_message(signal, signal_number, candle_info)
                        sent = self.broadcast_message(message)

                        # Save to history (signal dict now contains target_candle_close)
                        signal_record = {
                            'number': signal_number,
                            'date': datetime.now().date().isoformat(),
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'timestamp': datetime.now().isoformat(),
                            'type': signal['type'],
                            'prediction': signal['prediction'],
                            'polymarket_bet': signal['polymarket_bet'],
                            'confidence': signal['confidence'],
                            'confluence': signal['confluence'],
                            'price': signal['price'],
                            'rsi': signal['rsi'],
                            'target_candle_close': signal['target_candle_close'],  # CRITICAL for verification
                            'trade_candle': signal['trade_candle'],  # CURRENT or NEXT
                            'result': None,  # Will be updated after candle closes
                            'actual_direction': None,
                            'actual_price': None,
                            'verified_at': None
                        }

                        self.signals_history.append(signal_record)
                        self.save_signals_history()

                        self.last_signal_time = datetime.now()
                        print(f"   ✅ Sent to {sent} subscribers")
                        print(f"   🕐 Trade {signal['trade_candle']} candle")
                        print(f"   ⏳ Will verify at {candle_info['current_candle_close' if signal['trade_candle'] == 'CURRENT' else 'next_candle_close'].strftime('%H:%M')}")

                        # Start verification thread (runs in background)
                        verify_thread = threading.Thread(
                            target=self.verify_signal_result,
                            args=(signal_record,)
                        )
                        verify_thread.daemon = True
                        verify_thread.start()

                    else:
                        current = df.iloc[-1]
                        print(f"   ℹ️  No signal | BTC: ${current['close']:,.2f} | RSI: {current['rsi']:.1f}")

                time.sleep(check_interval)

            except KeyboardInterrupt:
                print("\n\n👋 Bot stopped")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(60)


def main():
    print("="*60)
    print("TELEGRAM SIGNAL BOT WITH RESULT TRACKING")
    print("="*60)
    print()

    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Configure your BOT_TOKEN first!")
        return

    bot = SignalTrackingBot(bot_token=BOT_TOKEN)
    bot.run(check_interval=60)


if __name__ == "__main__":
    main()
