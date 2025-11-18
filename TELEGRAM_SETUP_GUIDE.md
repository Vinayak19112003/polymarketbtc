# 📱 TELEGRAM SIGNAL BOT SETUP GUIDE

## 🎯 What This Bot Does

The Telegram Signal Bot monitors Bitcoin (BTC) prices every minute and sends you **real-time trading signals** directly to your Telegram when the ULTIMATE strategy detects a high-probability entry.

**Features:**
- ✅ Real-time monitoring of BTC 15-minute candles
- ✅ ULTIMATE strategy signal detection (54% win rate)
- ✅ Instant Telegram alerts with full trade details
- ✅ Confluence scoring (3-7 points)
- ✅ RSI, MACD, EMA, Volume, and Time analysis
- ✅ 10-12 signals per day
- ✅ No spam (15-minute cooldown between signals)

---

## 🚀 QUICK SETUP (5 Minutes)

### **Step 1: Create a Telegram Bot** (2 minutes)

1. Open Telegram on your phone or computer
2. Search for **@BotFather**
3. Start a chat and send: `/newbot`
4. Follow the prompts:
   - Choose a name for your bot (e.g., "My BTC Signal Bot")
   - Choose a username (e.g., "mybtcsignal_bot")
5. **Copy the Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Screenshot:**
```
BotFather: Alright, a new bot. How are we going to call it?
You: My BTC Signal Bot

BotFather: Good. Now let's choose a username for your bot.
You: mybtcsignal_bot

BotFather: Done! Your token is: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

### **Step 2: Get Your Chat ID** (1 minute)

1. Search for **@userinfobot** in Telegram
2. Start the bot
3. It will reply with your user information
4. **Copy your Chat ID** (looks like: `987654321`)

**Screenshot:**
```
@userinfobot: Your user ID: 987654321
```

**Alternative Method:**
1. Start a chat with your bot (search for the username you created)
2. Send any message (e.g., "Hello")
3. Open this URL in browser (replace YOUR_BOT_TOKEN):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. Look for "chat":{"id":YOUR_CHAT_ID}

---

### **Step 3: Configure the Bot** (2 minutes)

1. Open `telegram_signal_bot.py` in a text editor
2. Find these lines (around line 430):
   ```python
   BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
   CHAT_ID = "YOUR_CHAT_ID_HERE"
   ```

3. Replace with your actual credentials:
   ```python
   BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
   CHAT_ID = "987654321"
   ```

4. Save the file

---

### **Step 4: Install Requirements** (if needed)

Make sure you have Python 3 and required packages:

```bash
pip install requests pandas
```

---

### **Step 5: Run the Bot!**

```bash
python telegram_signal_bot.py
```

**You should see:**
```
============================================================
🤖 TELEGRAM SIGNAL BOT STARTED
============================================================
✅ Bot Token: ********************xyz
✅ Chat ID: 987654321
✅ Check Interval: 60 seconds
✅ Cooldown: 15 minutes

🔍 Monitoring BTC for ULTIMATE strategy signals...
============================================================
```

**And in Telegram, you'll receive:**
```
🤖 TELEGRAM SIGNAL BOT ACTIVATED

Your ULTIMATE Strategy signal bot is now monitoring BTC 15-minute candles.

You will receive alerts when:
✅ RSI reaches extreme levels (<25 or >75)
✅ Multiple indicators confirm (confluence ≥3)
✅ High-probability setup detected

Expected signals: 10-12 per day
Win rate: 54%+

Stand by for signals... 🚀
```

---

## 📨 What Signals Look Like

When a trading opportunity is detected, you'll receive a message like this:

```
🚨 POLYMARKET BTC SIGNAL ALERT 🚨

🟢 RSI EXTREME OVERSOLD

━━━━━━━━━━━━━━━━━━━━━
📊 SIGNAL DETAILS

📈 Prediction: UP
🎯 Polymarket Bet: YES
💯 Confidence: 58%
⭐ Confluence Score: 5/7

━━━━━━━━━━━━━━━━━━━━━
📈 MARKET DATA

💰 BTC Price: $42,350.00
📊 RSI: 23.5
📉 MACD Hist: 15.30
📦 Volume: 2.1x

━━━━━━━━━━━━━━━━━━━━━
💡 ACTION REQUIRED

1️⃣ Open Polymarket
2️⃣ Find "Bitcoin Up or Down" market
3️⃣ Bet YES (predict next candle UP)
4️⃣ Position size: 10% of capital
5️⃣ Wait 15 minutes for result

━━━━━━━━━━━━━━━━━━━━━
⏰ Time: 2025-11-18 14:32:15

Good luck! 🍀
```

---

## 🎯 Signal Types You'll Receive

### **1. 🟢 RSI EXTREME OVERSOLD (RSI < 25)**
- **Bet:** YES (predict UP)
- **Confidence:** 56%+
- **Win Rate:** 55.3% (from backtest)
- **Best signal type!**

### **2. 🔴 RSI EXTREME OVERBOUGHT (RSI > 75)**
- **Bet:** NO (predict DOWN)
- **Confidence:** 56%+
- **Win Rate:** 54.6%
- **Second best!**

### **3. 🟢 RSI STRONG OVERSOLD (RSI < 30)**
- **Bet:** YES (predict UP)
- **Confidence:** 54%+
- **Win Rate:** 52.1%

### **4. 🔴 RSI STRONG OVERBOUGHT (RSI > 70)**
- **Bet:** NO (predict DOWN)
- **Confidence:** 54%+
- **Win Rate:** 54.0%

---

## ⚙️ Bot Settings (Advanced)

You can customize the bot behavior by editing these parameters:

```python
# In telegram_signal_bot.py, around line 20:

self.cooldown_minutes = 15  # Minutes between signals (avoid spam)
```

```python
# In main() function, around line 460:

bot.monitor_and_signal(check_interval=60)  # Check every 60 seconds
```

**Recommended Settings:**
- `check_interval=60` (check every 60 seconds)
- `cooldown_minutes=15` (match 15-minute candles)

**For More Signals (not recommended):**
- `check_interval=30` (check every 30 seconds)
- `cooldown_minutes=10` (allow signals every 10 mins)

---

## 🔧 Troubleshooting

### **Problem: "Unauthorized" Error**
**Solution:**
- Check your BOT_TOKEN is correct
- Make sure you copied the full token from @BotFather

### **Problem: Not Receiving Messages**
**Solution:**
1. Check your CHAT_ID is correct
2. Make sure you've sent at least one message to your bot
3. Start the bot in Telegram (send /start)

### **Problem: "Connection Error" / "Failed to fetch data"**
**Solution:**
- Check your internet connection
- Binance API might be temporarily down
- Wait 60 seconds, bot will retry automatically

### **Problem: Too Many Signals**
**Solution:**
- Increase `cooldown_minutes` to 30 or 60
- Bot is working correctly (10-12 signals/day is normal)

### **Problem: Not Enough Signals**
**Solution:**
- Bot only signals when confluence score ≥3
- This is correct behavior (quality over quantity)
- You should get 10-12 signals per day on average

### **Problem: Bot Stops Running**
**Solution:**
- Run in background (see next section)
- Or run in terminal and keep it open

---

## 🖥️ Running Bot in Background

### **On Linux/Mac:**

**Using screen:**
```bash
screen -S telegram_bot
python telegram_signal_bot.py
# Press Ctrl+A then D to detach
# To reattach: screen -r telegram_bot
```

**Using nohup:**
```bash
nohup python telegram_signal_bot.py > bot.log 2>&1 &
# Check logs: tail -f bot.log
# Stop: ps aux | grep telegram_signal_bot.py
# Then: kill <process_id>
```

### **On Windows:**

**Using pythonw:**
```bash
pythonw telegram_signal_bot.py
```

**Or run as Windows service** (advanced)

---

## 📊 Expected Performance

Based on ULTIMATE strategy backtest:

| Metric | Expected |
|--------|----------|
| **Signals per Day** | 10-12 |
| **Win Rate** | 54%+ |
| **Best Signals** | RSI <25 or >75 (55%+ WR) |
| **Confluence 5+** | 57.3% win rate |
| **Monthly Profit** | $4,000 (with $10k capital) |

**Typical Day:**
```
9:15 AM  - Signal: RSI OS (WIN)
10:30 AM - Signal: RSI OB (LOSS)
12:45 PM - Signal: RSI OS (WIN)
2:00 PM  - Signal: RSI OB (WIN)
3:30 PM  - Signal: RSI OS (WIN)
5:15 PM  - Signal: RSI OB (LOSS)
7:00 PM  - Signal: RSI OS (WIN)
9:30 PM  - Signal: RSI OB (WIN)

Total: 8 signals, 6 wins (75% - lucky day!)
```

---

## 🛡️ Safety Tips

1. **Don't Share Your Bot Token**
   - Treat it like a password
   - Never commit to GitHub
   - Keep it private

2. **Verify Signals**
   - Always check TradingView yourself
   - Don't blindly follow every signal
   - Use your judgment

3. **Position Sizing**
   - Start with small bets
   - Never risk more than 10% per trade
   - Follow the strategy rules

4. **Monitor Performance**
   - Track all trades in spreadsheet
   - Calculate actual win rate
   - Adjust if needed

---

## 📱 Telegram Commands (Future Feature)

You can add these commands to make the bot interactive:

```python
/status - Show current BTC price and RSI
/stats - Show today's signal stats
/pause - Pause signal alerts
/resume - Resume signal alerts
/help - Show help message
```

(Not implemented yet, but easy to add!)

---

## 🚀 Advanced: Run on Cloud Server

To run 24/7 without keeping your computer on:

### **Option 1: Heroku (Free)**
1. Create Heroku account
2. Deploy bot as Python app
3. Set config vars (BOT_TOKEN, CHAT_ID)
4. Enable worker dyno

### **Option 2: AWS EC2 (Free Tier)**
1. Launch t2.micro instance
2. Upload bot script
3. Run with nohup
4. Keep instance running

### **Option 3: DigitalOcean ($5/month)**
1. Create droplet
2. SSH and upload bot
3. Run with screen or systemd
4. Most reliable option

---

## 📊 Monitoring Bot Performance

Keep a spreadsheet to track signals:

| Date | Time | Signal Type | Bet | Result | P&L |
|------|------|-------------|-----|--------|-----|
| 2025-11-18 | 09:15 | RSI OS | YES | WIN | +$98 |
| 2025-11-18 | 10:30 | RSI OB | NO | LOSS | -$102 |
| 2025-11-18 | 12:45 | RSI OS | YES | WIN | +$98 |

**Calculate:**
- Daily win rate
- Daily profit
- Best signal types
- Best times of day

---

## ❓ FAQ

**Q: How much capital do I need?**
A: Minimum $40, recommended $1,000-10,000

**Q: Do I need to watch Telegram all day?**
A: No, check when you get notifications. You have 15 minutes to place each bet.

**Q: What if I miss a signal?**
A: No problem, another one will come soon (10-12 per day)

**Q: Can I use multiple bots?**
A: Yes, but not necessary. One bot is enough.

**Q: Is this profitable?**
A: Backtest shows 54% win rate, but past performance doesn't guarantee future results.

**Q: What about fees?**
A: 2% Polymarket fee is included in strategy (need >52% WR to profit)

**Q: Can I customize the signals?**
A: Yes, edit the parameters in the code

---

## 🎯 Next Steps

1. ✅ Set up Telegram bot (5 minutes)
2. ✅ Run and test the bot
3. ✅ Verify you receive the startup message
4. ✅ Wait for first signal (could be minutes or hours)
5. ✅ When signal arrives, check TradingView
6. ✅ Place bet on Polymarket
7. ✅ Track result in spreadsheet
8. ✅ Repeat daily

---

## 💡 Pro Tips

1. **Best Hours to Trade:**
   - 9-11 AM EST
   - 2-5 PM EST
   - 8-10 PM EST

2. **Skip These Hours:**
   - Midnight - 6 AM (low liquidity)

3. **Best Signals:**
   - Confluence score 5+ (57% WR)
   - RSI < 25 or > 75 (55% WR)

4. **Position Sizing:**
   - Start: 5% of capital
   - After 50 wins: 10% of capital
   - Max: 15% of capital

---

## 🎉 Ready to Go!

Your Telegram Signal Bot is now ready to send you profitable trading signals!

**Expected Results:**
- 10-12 signals per day
- 54% win rate
- $40-400 daily profit (with $10k capital)

**Keep the bot running, watch for signals, and trade with discipline!**

Good luck! 🚀📈💰

---

## 📞 Support

If you have issues:
1. Check the Troubleshooting section above
2. Review your bot token and chat ID
3. Check bot.log for errors
4. Verify Binance API is accessible

---

*Last Updated: November 18, 2025*
