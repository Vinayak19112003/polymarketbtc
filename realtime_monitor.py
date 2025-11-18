"""
Real-Time BTC Streak Monitor
WebSocket connection to Binance for live 15m candle tracking
Generates trading signals in real-time
"""

import json
import time
import websocket
import threading
from datetime import datetime
from collections import deque
import pandas as pd
import requests


class RealtimeBTCMonitor:
    """Monitor BTC price in real-time and detect streak patterns"""

    def __init__(self, interval='15m', lookback=20, signal_callback=None):
        """
        Args:
            interval: Candle interval (15m, 5m, 1h, etc.)
            lookback: Number of candles to maintain for streak detection
            signal_callback: Function to call when signal is generated
        """
        self.interval = interval
        self.lookback = lookback
        self.signal_callback = signal_callback

        # Store recent candles
        self.candles = deque(maxlen=lookback)

        # Current candle being formed
        self.current_candle = None

        # WebSocket
        self.ws = None
        self.ws_thread = None
        self.running = False

        # Signal rules (from backtest analysis)
        self.signal_rules = self._load_signal_rules()

    def _load_signal_rules(self):
        """Load trading signal rules from analysis"""
        # These would normally be loaded from your analysis results
        # For now, using example rules
        return [
            {"streak_length": 3, "direction": "UP", "action": "BET_REVERSAL", "prediction": "DOWN", "min_prob": 0.55},
            {"streak_length": 3, "direction": "DOWN", "action": "BET_REVERSAL", "prediction": "UP", "min_prob": 0.55},
            {"streak_length": 4, "direction": "UP", "action": "BET_REVERSAL", "prediction": "DOWN", "min_prob": 0.60},
            {"streak_length": 4, "direction": "DOWN", "action": "BET_REVERSAL", "prediction": "UP", "min_prob": 0.60},
            {"streak_length": 5, "direction": "UP", "action": "BET_REVERSAL", "prediction": "DOWN", "min_prob": 0.65},
            {"streak_length": 5, "direction": "DOWN", "action": "BET_REVERSAL", "prediction": "UP", "min_prob": 0.65},
        ]

    def fetch_historical_candles(self):
        """Fetch recent candles to initialize the buffer"""
        print(f"📊 Fetching last {self.lookback} candles for initialization...")

        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={self.interval}&limit={self.lookback}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for candle in data:
                self._process_candle({
                    "timestamp": candle[0],
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5])
                })

            print(f"✅ Loaded {len(self.candles)} historical candles")
            return True

        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return False

    def _process_candle(self, candle_data):
        """Process and store a completed candle"""
        candle = {
            "timestamp": datetime.fromtimestamp(candle_data["timestamp"] / 1000),
            "open": candle_data["open"],
            "high": candle_data["high"],
            "low": candle_data["low"],
            "close": candle_data["close"],
            "volume": candle_data["volume"],
            "direction": "UP" if candle_data["close"] > candle_data["open"]
                        else "DOWN" if candle_data["close"] < candle_data["open"]
                        else "NEUTRAL"
        }

        self.candles.append(candle)

    def calculate_current_streak(self):
        """Calculate the current streak from stored candles"""
        if len(self.candles) < 2:
            return None, 0

        current_direction = self.candles[-1]["direction"]
        if current_direction == "NEUTRAL":
            return None, 0

        streak_length = 1

        # Count backwards
        for i in range(len(self.candles) - 2, -1, -1):
            if self.candles[i]["direction"] == current_direction:
                streak_length += 1
            else:
                break

        return current_direction, streak_length

    def check_for_signals(self):
        """Check if current streak matches any trading signals"""
        direction, streak_length = self.calculate_current_streak()

        if not direction:
            return None

        # Check against signal rules
        for rule in self.signal_rules:
            if rule["streak_length"] == streak_length and rule["direction"] == direction:
                signal = {
                    "timestamp": datetime.now(),
                    "streak_direction": direction,
                    "streak_length": streak_length,
                    "action": rule["action"],
                    "prediction": rule["prediction"],
                    "current_price": self.candles[-1]["close"],
                    "rule": rule
                }

                print(f"\n🚨 SIGNAL DETECTED!")
                print(f"   Time: {signal['timestamp']}")
                print(f"   Streak: {streak_length} consecutive {direction} candles")
                print(f"   Action: {rule['action']} → Predict {rule['prediction']}")
                print(f"   Current Price: ${signal['current_price']:,.2f}")

                # Call callback if provided
                if self.signal_callback:
                    self.signal_callback(signal)

                return signal

        return None

    def on_message(self, ws, message):
        """Handle WebSocket message"""
        try:
            data = json.loads(message)

            # Binance kline websocket format
            if 'k' in data:
                kline = data['k']

                # Check if candle is closed
                if kline['x']:  # x = is candle closed
                    candle_data = {
                        "timestamp": kline['t'],
                        "open": float(kline['o']),
                        "high": float(kline['h']),
                        "low": float(kline['l']),
                        "close": float(kline['c']),
                        "volume": float(kline['v'])
                    }

                    self._process_candle(candle_data)

                    # Check for signals on new completed candle
                    self.check_for_signals()

                    # Print update
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] New {self.interval} candle: "
                          f"O:{candle_data['open']:.2f} H:{candle_data['high']:.2f} "
                          f"L:{candle_data['low']:.2f} C:{candle_data['close']:.2f} "
                          f"({self.candles[-1]['direction']})")

        except Exception as e:
            print(f"❌ Error processing message: {e}")

    def on_error(self, ws, error):
        """Handle WebSocket error"""
        print(f"❌ WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        print(f"🔌 WebSocket connection closed")
        self.running = False

    def on_open(self, ws):
        """Handle WebSocket open"""
        print(f"✅ WebSocket connected - monitoring BTC {self.interval} candles")
        self.running = True

    def start(self):
        """Start real-time monitoring"""
        print("=" * 80)
        print("🚀 STARTING REAL-TIME BTC STREAK MONITOR")
        print("=" * 80)

        # Fetch historical data first
        if not self.fetch_historical_candles():
            print("⚠️  Starting without historical data")

        # Check initial state
        direction, streak_length = self.calculate_current_streak()
        if direction:
            print(f"📊 Current streak: {streak_length} consecutive {direction} candles")

        # Start WebSocket connection
        ws_url = f"wss://stream.binance.com:9443/ws/btcusdt@kline_{self.interval}"
        print(f"🔌 Connecting to: {ws_url}")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        # Run WebSocket in separate thread
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        print("\n✅ Monitor running. Press Ctrl+C to stop.\n")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping monitor...")
            self.stop()

    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.ws:
            self.ws.close()
        print("✅ Monitor stopped")


def signal_handler(signal):
    """Example callback function for when a signal is detected"""
    print(f"\n📢 CUSTOM HANDLER: Signal received!")
    print(f"   You should: {signal['action']}")
    print(f"   Predicted next direction: {signal['prediction']}")
    print(f"   Consider placing a Polymarket bet!\n")

    # Here you would:
    # 1. Call Polymarket API to place bet
    # 2. Send Telegram notification
    # 3. Log to database
    # 4. Update portfolio


def main():
    """Main entry point for real-time monitoring"""
    monitor = RealtimeBTCMonitor(
        interval='15m',
        lookback=20,
        signal_callback=signal_handler
    )

    monitor.start()


if __name__ == "__main__":
    main()
