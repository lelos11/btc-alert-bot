import os
import asyncio
from telegram import Bot
from telegram.ext import Application, ContextTypes, CommandHandler
import requests
from datetime import datetime, time
import math

# Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class BTCDCAStrategy:
    """BTC DCA Strategy με Power Law Divergence"""
    
    GENESIS_DATE = datetime(2009, 1, 3)
    P1_DATE = datetime(2019, 11, 18)
    P1_PRICE = 10638
    P1_DIVERGENCE = -27.5
    
    P2_DATE = datetime(2026, 1, 12)
    P2_PRICE = 91100
    P2_DIVERGENCE = -27.9
    
    @staticmethod
    def get_btc_price():
        """Λήψη τιμής από Kraken"""
        try:
            url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
            response = requests.get(url, timeout=10)
            data = response.json()
            price = float(data['result']['XXBTZUSD']['c'][0])
            return price
        except:
            try:
                url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
                response = requests.get(url, timeout=10)
                return response.json()['bitcoin']['usd']
            except:
                return None
    
    @staticmethod
    def get_fear_greed():
        """Λήψη Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            return int(response.json()['data'][0]['value'])
        except:
            return None
    
    @classmethod
    def calculate_power_law_price(cls):
        """Υπολογισμός Power Law price με calibration"""
        days_since_genesis = (datetime.now() - cls.GENESIS_DATE).days
        
        p1_days = (cls.P1_DATE - cls.GENESIS_DATE).days
        p2_days = (cls.P2_DATE - cls.GENESIS_DATE).days
        
        p1_trend = cls.P1_PRICE / (1 + cls.P1_DIVERGENCE/100)
        p2_trend = cls.P2_PRICE / (1 + cls.P2_DIVERGENCE/100)
        
        b = (math.log(p2_trend) - math.log(p1_trend)) / (math.log(p2_days) - math.log(p1_days))
        a = p1_trend / (p1_days ** b)
        
        power_law_price = a * (days_since_genesis ** b)
        return power_law_price
    
    @classmethod
    def calculate_divergence(cls, btc_price, power_law_price):
        """Υπολογισμός divergence %"""
        divergence = ((btc_price - power_law_price) / power_law_price) * 100
        return divergence
    
    @classmethod
    def calculate_multiplier(cls, divergence, fear_greed):
        """Υπολογισμός DCA multiplier"""
        
        if divergence >= 0:
            base_multiplier = 1
        elif divergence >= -15:
            base_multiplier = 1
        elif divergence >= -30:
            base_multiplier = 2
        elif divergence >= -40:
            base_multiplier = 3
        else:
            base_multiplier = 5
        
        if divergence <= -30 and base_multiplier == 3:
            base_multiplier = 5
        
        if fear_greed <= 25 and divergence <= -15:
            if base_multiplier == 1:
                final_multiplier = 2
            elif base_multiplier == 2:
                final_multiplier = 3
            elif base_multiplier == 3:
                final_multiplier = 5
            else:
                final_multiplier = base_multiplier
        else:
            final_multiplier = base_multiplier
        
        return base_multiplier, final_multiplier
    
    @classmethod
    def calculate_sell_recommendation(cls, divergence):
        """Υπολογισμός sell %"""
        if 30 <= divergence <= 35:
            return 20, "Sell 20%"
        elif 50 <= divergence <= 55:
            return 25, "Sell 25%"
        elif divergence >= 70:
            return 30, "Sell 30%"
        else:
            return 0, "HOLD"
    
    @classmethod
    def analyze(cls):
        """Πλήρης ανάλυση"""
        btc_price = cls.get_btc_price()
        fear_greed = cls.get_fear_greed()
        power_law_price = cls.calculate_power_law_price()
        
        if btc_price is None or fear_greed is None:
            return None, "⚠️ Σφάλμα λήψης δεδομένων"
        
        divergence = cls.calculate_divergence(btc_price, power_law_price)
        base_mult, final_mult = cls.calculate_multiplier(divergence, fear_greed)
        sell_pct, sell_action = cls.calculate_sell_recommendation(divergence)
        
        message = "📊 *BTC DCA Strategy Analysis*\n\n"
        message += f"💰 BTC Price: ${btc_price:,.2f}\n"
        message += f"📈 Power Law: ${power_law_price:,.0f}\n"
        message += f"📉 Divergence: {divergence:+.1f}%\n"
        message += f"😨 Fear & Greed: {fear_greed}/100\n\n"
        
        message += "🎯 *DCA Strategy:*\n"
        message += f"Base Multiplier: x{base_mult}\n"
        message += f"Final Multiplier: *x{final_mult}*\n\n"
        
        if divergence < 0:
            message += f"🟢 *BUY SIGNAL: x{final_mult}*\n"
            message += f"_Αγόρασε {final_mult}x το base ποσό_"
        else:
            if sell_pct > 0:
                message += f"🔴 *{sell_action}*\n"
                message += f"_Πούλησε {sell_pct}% του portfolio_"
            else:
                message += "🟡 *HOLD*\n"
                message += "_Κρατάς - Περίμενε_"
        
        return final_mult, message

# Callback function
async def analysis_every_12h(context: ContextTypes.DEFAULT_TYPE):
    """Ανάλυση κάθε 12 ώρες"""
    _, message = BTCDCAStrategy.analyze()
    if message:
        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        print(f"✓ 12-hour analysis sent at {datetime.now()}")

# Command handlers
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "👋 *BTC DCA Strategy Bot!*\n\n"
        "🎯 Based on Excel rules\n"
        "📊 Power Law Divergence\n"
        "😨 Fear & Greed Index\n\n"
        "Εντολές:\n"
        "/analyze - Τρέχουσα ανάλυση\n"
        "/price - Τιμή BTC (Kraken)"
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def analyze_now(update, context: ContextTypes.DEFAULT_TYPE):
    _, message = BTCDCAStrategy.analyze()
    await update.message.reply_text(message, parse_mode='Markdown')

async def get_price(update, context: ContextTypes.DEFAULT_TYPE):
    price = BTCDCAStrategy.get_btc_price()
    if price:
        await update.message.reply_text(f"💰 Bitcoin (Kraken): ${price:,.2f}")
    else:
        await update.message.reply_text("⚠️ Σφάλμα λήψης τιμής")

def main():
    print("🤖 Starting BTC DCA Strategy Bot...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_now))
    application.add_handler(CommandHandler("price", get_price))
    
    job_queue = application.job_queue
    
    # Έλεγχος κάθε 12 ώρες
    job_queue.run_repeating(
        analysis_every_12h,
        interval=43200,  # 12 ώρες = 43200 δευτερόλεπτα
        first=10
    )
    print("✓ Analysis every 12 hours enabled")
    
    print("✓ Bot is running!")
    application.run_polling(allowed_updates=['message'])

if __name__ == "__main__":
    main()





