import asyncio
from telegram import Bot
from telegram.ext import Application, ContextTypes, CommandHandler
import requests
from datetime import datetime

# ========== ΡΥΘΜΙΣΕΙΣ - ΑΛΛΑΞΕ ΤΑ ΠΑΡΑΚΑΤΩ ==========
TELEGRAM_TOKEN = "8299285517:AAFVk7teghc2tAtp2zzofBfAHAcYemPSKUE"
TELEGRAM_CHAT_ID = "896487510"
# =====================================================

class BTCAnalyzer:
    """Κλάση για ανάλυση Bitcoin"""
    
    @staticmethod
    def get_btc_price():
        """Λήψη τρέχουσας τιμής BTC"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            return response.json()['bitcoin']['usd']
        except Exception as e:
            print(f"Error fetching BTC price: {e}")
            return None
    
    @staticmethod
    def get_fear_greed():
        """Λήψη Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            return int(response.json()['data'][0]['value'])
        except Exception as e:
            print(f"Error fetching Fear & Greed: {e}")
            return None
    
    @staticmethod
    def calculate_power_law():
        """Υπολογισμός Power Law τιμής"""
        genesis = datetime(2009, 1, 3)
        days = (datetime.now() - genesis).days
        # Διορθωμένος τύπος: 10^(-17) * days^5.82
        return (10 ** -17) * (days ** 5.82)


    
    @classmethod
    def analyze(cls):
        """Πλήρης ανάλυση BTC"""
        btc_price = cls.get_btc_price()
        fear_greed = cls.get_fear_greed()
        power_law_price = cls.calculate_power_law()
        
        if btc_price is None or fear_greed is None:
            return None, "⚠️ Σφάλμα λήψης δεδομένων"
        
        buy_signals = 0
        reasons = []
        
        # Ανάλυση Power Law
        if btc_price < power_law_price:
            buy_signals += 1
            reasons.append(f"✅ Τιμή κάτω από Power Law (${btc_price:,.0f} < ${power_law_price:,.0f})")
        else:
            reasons.append(f"❌ Τιμή πάνω από Power Law (${btc_price:,.0f} > ${power_law_price:,.0f})")
        
        # Ανάλυση Fear & Greed
        if fear_greed < 25:
            buy_signals += 1
            reasons.append(f"✅ Extreme Fear ({fear_greed}/100) - Ευκαιρία αγοράς")
        elif fear_greed < 50:
            reasons.append(f"🟡 Fear ({fear_greed}/100)")
        elif fear_greed < 75:
            reasons.append(f"🟠 Greed ({fear_greed}/100)")
        else:
            reasons.append(f"🔴 Extreme Greed ({fear_greed}/100) - Προσοχή!")
        
        # Δημιουργία μηνύματος
        message = "📊 *Bitcoin Analysis Alert*\n\n"
        message += f"💰 Τιμή: ${btc_price:,.2f}\n"
        message += f"📈 Power Law: ${power_law_price:,.0f}\n"
        message += f"😨 Fear & Greed: {fear_greed}/100\n\n"
        message += "\n".join(reasons)
        message += f"\n\n🎯 *Σήματα Αγοράς: {buy_signals}/2*\n\n"
        
        # Σύσταση
        if buy_signals >= 2:
            message += "🟢 *ΣΥΣΤΑΣΗ: ΚΑΛΗ ΜΕΡΑ ΓΙΑ ΑΓΟΡΑ!*"
            is_buy_signal = True
        elif buy_signals == 1:
            message += "🟡 *ΣΥΣΤΑΣΗ: ΟΥΔΕΤΕΡΗ - ΑΝΑΜΟΝΗ*"
            is_buy_signal = False
        else:
            message += "🔴 *ΣΥΣΤΑΣΗ: ΟΧI ΚΑΛΗ ΣΤΙΓΜΗ*"
            is_buy_signal = False
        
        return is_buy_signal, message

# ========== CALLBACK FUNCTIONS ==========

async def send_periodic_analysis(context: ContextTypes.DEFAULT_TYPE):
    """Στέλνει ανάλυση κάθε X ώρες"""
    _, message = BTCAnalyzer.analyze()
    if message:
        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        print(f"✓ Periodic alert sent at {datetime.now()}")

async def send_buy_signal_only(context: ContextTypes.DEFAULT_TYPE):
    """Στέλνει alert ΜΟΝΟ αν υπάρχει σήμα αγοράς"""
    is_buy_signal, message = BTCAnalyzer.analyze()
    if is_buy_signal:
        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"🚨 *BUY ALERT!* 🚨\n\n{message}",
            parse_mode='Markdown'
        )
        print(f"✓ BUY SIGNAL alert sent at {datetime.now()}")
    else:
        print(f"✗ No buy signal at {datetime.now()}")

# ========== COMMAND HANDLERS ==========

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    """Εντολή /start"""
    welcome = (
        "👋 *Καλώς ήρθες στο BTC Alert Bot!*\n\n"
        "Εντολές:\n"
        "/analyze - Τρέχουσα ανάλυση\n"
        "/price - Τιμή BTC\n"
        "/help - Βοήθεια"
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def analyze_now(update, context: ContextTypes.DEFAULT_TYPE):
    """Εντολή /analyze"""
    _, message = BTCAnalyzer.analyze()
    await update.message.reply_text(message, parse_mode='Markdown')

async def get_price(update, context: ContextTypes.DEFAULT_TYPE):
    """Εντολή /price"""
    price = BTCAnalyzer.get_btc_price()
    if price:
        await update.message.reply_text(f"💰 Bitcoin: ${price:,.2f}")
    else:
        await update.message.reply_text("⚠️ Σφάλμα λήψης τιμής")

# ========== MAIN ==========

def main():
    """Εκκίνηση bot με alerts"""
    
    print("🤖 Starting BTC Alert Bot...")
    
    # Δημιουργία Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Προσθήκη command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_now))
    application.add_handler(CommandHandler("price", get_price))
    
    # ========== ΡΥΘΜΙΣΗ ALERTS ==========
    job_queue = application.job_queue
    
    # Ανάλυση κάθε 6 ώρες
    job_queue.run_repeating(
        send_periodic_analysis,
        interval=21600,
        first=10
    )
    print("✓ Periodic alerts enabled (every 6 hours)")
    
    # Alert ΜΟΝΟ όταν υπάρχει σήμα αγοράς (έλεγχος κάθε 1 ώρα)
    job_queue.run_repeating(
        send_buy_signal_only,
        interval=3600,
        first=15
    )
    print("✓ Buy signal alerts enabled (checked every hour)")
    
    # Εκκίνηση
    print("✓ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=['message'])

if __name__ == "__main__":
    main()
