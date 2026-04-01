from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import threading
import time

app = Flask(__name__)

TELEGRAM_TOKEN = "8760124700:AAG1UG8FpfETC3wBhvleqMaIpXi8FUvek8A"
CHAT_ID = "635329910"

BIST_HISSELER = [
    "ACSEL","ADEL","ADESE","AEFES","AFYON","AGESA","AGHOL","AKBNK","AKCNS",
    "AKFEN","AKGRT","AKSA","AKSEN","ALARK","ALBRK","ALFAS","ALKIM","ALVES",
    "ANELE","ARCLK","ARDYZ","ARENA","ARSAN","ASELS","ASTOR","AYCES","AYEN",
    "AYGAZ","BAGFS","BALSU","BANVT","BERA","BIMAS","BINBN","BINHO","BIZIM",
    "BJKAS","BORSK","BOSSA","BRISA","BRSAN","BSOKE","BTCIM","BUCIM","BURCE",
    "CCOLA","CELHA","CEMAS","CEMTS","CIMSA","CLEBI","COFAZ","CWENE","DOAS",
    "DOHOL","ECILC","ECZYT","EGEEN","EGGUB","EKGYO","EMKEL","ENJSA","ENKAI",
    "ERGL","ETILR","FADE","FENER","FROTO","GARFA","GEDZA","GEREL","GESAN",
    "GLYHO","GOLTS","GOODY","GSDHO","GSRAY","GUBRF","HALKB","HATEK","HEKTS",
    "HOROZ","HTTBT","IHAAS","IHLAS","INDES","INFO","INVEO","ISGYO","JANTS",
    "KAREL","KARSN","KARTN","KCAER","KCHOL","KENT","KERVT","KGYO","KIMMR",
    "KLNMA","KMPUR","KONYA","KORDS","KOZAA","KOZAL","KRDMD","KTLEV","KUTPO",
    "LIDER","LOGO","MAALT","MAKIM","MANAS","MAVI","MEGAP","MERCN","MERIT",
    "MERKO","MGROS","MPARK","MRSHL","MUTLU","NETAS","NTHOL","NTTUR","NUHCM",
    "ODAS","OTKAR","OYAKC","PETKM","PETUN","PGSUS","PKART","POLHO","PRKAB",
    "PTOFS","QNBFB","RAYSG","RGYAS","SAHOL","SANEL","SANFM","SARKY","SASA",
    "SISE","SKBNK","SOKM","TATGD","TAVHL","TCELL","TDGYO","THYAO","TOASO",
    "TOFAS","TRGYO","TSKB","TTKOM","TTRAK","TUPRS","TURGG","TURSG","ULKER",
    "VAKBN","VAKKO","VESBE","VESTL","YAPRK","YGYO","YUNSA","ZEDUR","ZRGYO"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_signals(ticker):
    try:
        df = yf.download(f"{ticker}.IS", period="6mo", interval="1d", progress=False, auto_adjust=True)
        if df is None or len(df) < 50:
            return None
        close = df["Close"].squeeze()
        high  = df["High"].squeeze()
        low   = df["Low"].squeeze()
        volume = df["Volume"].squeeze()

        e21  = ta.ema(close, 21)
        e50  = ta.ema(close, 50)
        rsi  = ta.rsi(close, 14)
        mom  = ta.mom(close, 10)
        adx_df = ta.adx(high, low, close, 14)
        adx  = adx_df["ADX_14"]
        stoch = ta.stoch(high, low, close, 9, 3, 3)
        k = stoch["STOCHk_9_3_3"]
        d = stoch["STOCHd_9_3_3"]
        stochrsi = ta.stochrsi(close, 3, 3, 14, 14)
        stochrsi_d = stochrsi["STOCHRSId_14_14_3_3"]
        vol_avg10 = volume.rolling(10).mean()
        vol_avg20 = volume.rolling(20).mean()

        i = -1
        p = -2

        bull = close.iloc[i] > e50.iloc[i] and e21.iloc[i] > e50.iloc[i]
        bear = close.iloc[i] < e50.iloc[i] and e21.iloc[i] < e50.iloc[i]

        k_cross_over   = k.iloc[p] < d.iloc[p] and k.iloc[i] > d.iloc[i]
        k_cross_under  = k.iloc[p] > d.iloc[p] and k.iloc[i] < d.iloc[i]
        close_cross_e21 = close.iloc[p] < e21.iloc[p] and close.iloc[i] > e21.iloc[i]
        rsi_cross_30   = rsi.iloc[p] < 30 and rsi.iloc[i] > 30

        al    = bull and k_cross_over and k.iloc[i] < 60 and rsi.iloc[i] > 40
        sat   = bear and k_cross_under and k.iloc[i] > 40 and rsi.iloc[i] < 60
        ralli = (close.iloc[i] > e21.iloc[i] and close_cross_e21 and
                 rsi.iloc[i] > 50 and k.iloc[i] > d.iloc[i] and
                 volume.iloc[i] > vol_avg20.iloc[i])
        bot   = rsi.iloc[i] < 38 and k.iloc[i] < 28 and k_cross_over

        dip = (rsi_cross_30 and
               mom.iloc[i] > -10 and
               stochrsi_d.iloc[i] < 40 and
               volume.iloc[i] > vol_avg10.iloc[i] and
               adx.iloc[i] > 14)

        fiyat    = round(float(close.iloc[i]), 2)
        degisim  = round(float((close.iloc[i] - close.iloc[p]) / close.iloc[p] * 100), 2)
        rsi_val  = round(float(rsi.iloc[i]), 0)

        return {"al": al, "sat": sat, "ralli": ralli, "bot": bot, "dip": dip,
                "fiyat": fiyat, "degisim": degisim, "rsi": rsi_val}
    except:
        return None

def tara():
    send_telegram("🔍 <b>BIST Tarama Başlıyor...</b>")
    al_list    = []
    sat_list   = []
    ralli_list = []
    bot_list   = []
    dip_list   = []
    tarandi    = 0

    for hisse in BIST_HISSELER:
        sonuc = get_signals(hisse)
        if sonuc:
            tarandi += 1
            deg  = f"+{sonuc['degisim']}%" if sonuc['degisim'] >= 0 else f"{sonuc['degisim']}%"
            bilgi = f"<b>{hisse}</b>  {sonuc['fiyat']}  ({deg})  RSI:{int(sonuc['rsi'])}"
            if sonuc["ralli"]:
                ralli_list.append(bilgi)
            elif sonuc["al"]:
                al_list.append(bilgi)
            if sonuc["sat"]:
                sat_list.append(bilgi)
            if sonuc["bot"]:
                bot_list.append(bilgi)
            if sonuc["dip"]:
                dip_list.append(bilgi)

    mesaj = ""
    if al_list:
        mesaj += f"✅ <b>AL ({len(al_list)} hisse)</b>\n"
        mesaj += "\n".join([f"• {h}" for h in al_list]) + "\n\n"
    if ralli_list:
        mesaj += f"🚀 <b>RALLİ ({len(ralli_list)} hisse)</b>\n"
        mesaj += "\n".join([f"• {h}" for h in ralli_list]) + "\n\n"
    if sat_list:
        mesaj += f"🔴 <b>SAT ({len(sat_list)} hisse)</b>\n"
        mesaj += "\n".join([f"• {h}" for h in sat_list]) + "\n\n"
    if bot_list:
        mesaj += f"⬆️ <b>BOT AL ({len(bot_list)} hisse)</b>\n"
        mesaj += "\n".join([f"• {h}" for h in bot_list]) + "\n\n"
    if dip_list:
        mesaj += f"🎯 <b>RSI DİP ({len(dip_list)} hisse)</b>\n"
        mesaj += "\n".join([f"• {h}" for h in dip_list]) + "\n\n"

    mesaj += f"─────────────────────\n✅ {tarandi} hisse tarandı\n⏳ 60 dakika bekleniyor..."

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

def tarama_loop():
    while True:
        try:
            tara()
        except Exception as e:
            send_telegram(f"⚠️ Hata: {str(e)}")
        time.sleep(3600)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return "ok", 200
    sinyal = data.get("sinyal", "")
    hisse  = data.get("hisse", "")
    fiyat  = data.get("fiyat", "")
    tf     = data.get("tf", "")
    emoji  = {"AL":"✅","SAT":"🔴","RALLI":"🚀","BOT_AL":"⬆️"}.get(sinyal, "📊")
    mesaj  = f"{emoji} <b>{sinyal}</b>\n📈 Hisse: <b>{hisse}</b>\n💰 Fiyat: {fiyat}\n⏱ TF: {tf}"
    send_telegram(mesaj)
    return "ok", 200

@app.route("/")
def index():
    return "BIST ZKN Webhook Çalışıyor ✅"

if __name__ == "__main__":
    t = threading.Thread(target=tarama_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=8080)
