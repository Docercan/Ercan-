from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from pybit.unified_trading import HTTP
import pandas as pd
import pandas_ta as ta

# === AYARLAR ===
BOT_TOKEN = "<BOT_TOKEN>"   # BURAYA YENİ TOKEN
ALLOWED_USER_ID = 1501252778
BYBIT = HTTP(testnet=False)

# === GÜVENLİK ===
def yetki_kontrol(update):
    return update.effective_user.id == ALLOWED_USER_ID

# === ANALİZ FONKSİYONU ===
def analiz_yap(symbol, interval):
    klines = BYBIT.get_kline(
        category="linear",
        symbol=symbol,
        interval=interval,
        limit=200
    )["result"]["list"]

    df = pd.DataFrame(klines, columns=[
        "time","open","high","low","close","volume","turnover"
    ])
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df = pd.concat([df, macd], axis=1)

    rsi = df["rsi"].iloc[-1]
    macd_val = df["MACD_12_26_9"].iloc[-1]

    if rsi < 30:
        return "Aşırı satım, tepki gelebilir 📈"
    elif rsi > 70:
        return "Aşırı alım, geri çekilme riski ⚠️"
    elif macd_val > 0:
        return "Momentum yukarı 📈"
    else:
        return "Zayıf görünüm ⚠️"

# === TELEGRAM KOMUTU ===
async def analiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetki_kontrol(update):
        return  # Sessizce yok sayıyoruz, drama yok

    if len(context.args) == 0:
        await update.message.reply_text("Coin yaz. Örn: /analiz BTC")
        return

    coin = context.args[0].upper()
    symbol = coin + "USDT"

    sonuc = f"{symbol} Analiz 📊\n\n"

    zamanlar = {
        "5dk": 5,
        "15dk": 15,
        "30dk": 30,
        "1s": 60
    }

    for ad, sure in zamanlar.items():
        try:
            yorum = analiz_yap(symbol, sure)
            sonuc += f"{ad}: {yorum}\n"
        except:
            sonuc += f"{ad}: Veri alınamadı\n"

    await update.message.reply_text(sonuc)

# === BOTU BAŞLAT ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("analiz", analiz))
app.run_polling()
BOT_TOKEN = "<BOT_TOKEN>"
