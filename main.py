import os
os.environ["NUMBA_DISABLE_JIT"] = "1"

from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta
import borsapy as bp
import threading
import time
from datetime import datetime
import pytz

app = Flask(__name__)

TELEGRAM_TOKEN = "8760124700:AAG1UG8FpfETC3wBhvleqMaIpXi8FUvek8A"
CHAT_ID = "635329910"

YEDEK_HISSELER = [
    "ACSEL","ADEL","AEFES","AGESA","AKBNK","AKCNS","AKSA","AKSEN",
    "ALARK","ALBRK","ALKIM","ALVES","ANELE","ARCLK","ARDYZ","ARENA",
    "ASELS","ASTOR","AYEN","AYGAZ","BAGFS","BALSU","BANVT","BERA",
    "BIMAS","BINBN","BINHO","BIZIM","BJKAS","BORSK","BOSSA","BRISA",
    "BRSAN","BSOKE","BTCIM","BUCIM","BURCE","CCOLA","CELHA","CEMAS",
    "CEMTS","CIMSA","CLEBI","CWENE","DOAS","DOHOL","ECILC","ECZYT",
    "EGEEN","EGGUB","EKGYO","EMKEL","ENJSA","ENKAI","ERGL","ETILR",
    "FADE","FENER","FROTO","GARFA","GEDZA","GEREL","GESAN","GLYHO",
    "GOLTS","GOODY","GSDHO","GSRAY","GUBRF","HALKB","HATEK","HEKTS",
    "HOROZ","HTTBT","IHAAS","IHLAS","INDES","INFO","INVEO","ISGYO",
    "JANTS","KAREL","KARSN","KARTN","KCAER","KCHOL","KENT","KGYO",
    "KIMMR","KLNMA","KMPUR","KONYA","KORDS","KRDMD","KTLEV","KUTPO",
    "LIDER","LOGO","MAALT","MAKIM","MANAS","MAVI","MEGAP","MERCN",
    "MERIT","MERKO","MGROS","MPARK","MRSHL","NETAS","NTHOL","NUHCM",
    "ODAS","OTKAR","OYAKC","PETKM","PETUN","PGSUS","PKART","POLHO",
    "PRKAB","QNBFL","RAYSG","RGYAS","SAHOL","SANEL","SANFM","SARKY",
    "SASA","SISE","SKBNK","SOKM","TATGD","TAVHL","TCELL","TDGYO",
    "THYAO","TOASO","TRGYO","TSKB","TTKOM","TTRAK","TUPRS","TURGG",
    "TURSG","ULKER","VAKBN","VAKKO","VESBE","VESTL","YAPRK","YGYO",
    "YUNSA","ZEDUR","ZRGYO"
]

def get_all_hisseler():
    try:
        from tradingview_screener import Scanner
        scanner = Scanner.get_all_symbols(markets=["turkey"])
        hisseler = [s.replace("BIST:", "") for s in scanner]
        if len(hisseler) > 100:
            send_telegram(f"📋 Otomatik liste: {len(hisseler)} hisse bulundu.")
            return hisseler
        else:
            return YEDEK_HISSELER
    except Exception as e:
        return YEDEK_HISSELER

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def seans_acik():
    tz = pytz.timezone("Europe/Istanbul")
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return False
    baslangic = now.replace(hour=9, minute=30, second=0, microsecond=0)
    bitis = now.replace(hour=18, minute=30, second=0, microsecond=0)
    return baslangic <= now <= bitis

def get_data(ticker):
    try:
        hisse = bp.Ticker(ticker)
        df = hisse.history(period="6mo")
        if df is None or len(df) < 30:
            return None
        df = df.dropna()
        if len(df) < 30:
            return None
        close  = pd.Series(df["Close"].values, dtype=float)
        high   = pd.Series(df["High"].values, dtype=float)
        low    = pd.Series(df["Low"].values, dtype=float)
        volume = pd.Series(df["Volume"].values, dtype=float)
        return close, high, low, volume
    except:
        return None

def get_signals(ticker):
    try:
        result = get_data(ticker)
        if result is None:
            return None
        close, high, low, volume = result

        e21  = ta.ema(close, 21)
        e50  = ta.ema(close, 50)
        rsi  = ta.rsi(close, 14)
        mom  = ta.mom(close, 10)
        adx_df = ta.adx(high, low, close, 14)
        adx  = adx_df["ADX_14"]
        stoch = ta.stoch(high, low, close, 9, 3, 3)
        k = stoch.iloc[:, 0]
        d = stoch.iloc[:, 1]
        stochrsi = ta.stochrsi(close, 3, 3, 14, 14)
        stochrsi_d = stochrsi.iloc[:, 1]
        vol_avg10 = volume.rolling(10).mean()
        vol_avg20 = volume.rolling(20).mean()

        i = -1
        p = -2

        bull = float(close.iloc[i]) > float(e50.iloc[i]) and float(e21.iloc[i]) > float(e50.iloc[i])
        bear = float(close.iloc[i]) < float(e50.iloc[i]) and float(e21.iloc[i]) < float(e50.iloc[i])

        k_cross_over    = float(k.iloc[p]) < float(d.iloc[p]) and float(k.iloc[i]) > float(d.iloc[i])
        k_cross_under   = float(k.iloc[p]) > float(d.iloc[p]) and float(k.iloc[i]) < float(d.iloc[i])
        close_cross_e21 = float(close.iloc[p]) < float(e21.iloc[p]) and float(close.iloc[i]) > float(e21.iloc[i])
        rsi_cross_30    = float(rsi.iloc[p]) < 30 and float(rsi.iloc[i]) > 30

        al    = bull and k_cross_over and float(k.iloc[i]) < 60 and float(rsi.iloc[i]) > 40
        sat   = bear and k_cross_under and float(k.iloc[i]) > 40 and float(rsi.iloc[i]) < 60
        ralli = (float(close.iloc[i]) > float(e21.iloc[i]) and close_cross_e21 and
                 float(rsi.iloc[i]) > 50 and float(k.iloc[i]) > float(d.iloc[i]) and
                 float(volume.iloc[i]) > float(vol_avg20.iloc[i]))
        bot   = float(rsi.iloc[i]) < 38 and float(k.iloc[i]) < 28 and k_cross_over
        dip   = (rsi_cross_30 and float(mom.iloc[i]) > -10 and
                 float(stochrsi_d.iloc[i]) < 40 and
                 float(volume.iloc[i]) > float(vol_avg10.iloc[i]) and
                 float(adx.iloc[i]) > 14)

        fiyat   = round(float(close.iloc[i]), 2)
        degisim = round(float((close.iloc[i] - close.iloc[p]) / close.iloc[p] * 100), 2)
        rsi_val = round(float(rsi.iloc[i]), 0)

        return {"al": al, "sat": sat, "ralli": ralli, "bot": bot, "dip": dip,
                "fiyat": fiyat, "degisim": degisim, "rsi": rsi_val}
    except:
        return None

def get_guclu_trend(ticker):
    try:
        result = get_data(ticker)
        if result is None:
            return None
        close, high, low, volume = result

        e5  = ta.ema(close, 5)
        e13 = ta.ema(close, 13)
        psar_df = ta.psar(high, low, close)
        psar = psar_df.iloc[:, 0]
        cci = ta.cci(high, low, close, 20)
        vol_degisim = (volume.iloc[-1] - volume.iloc[-2]) / volume.iloc[-2] * 100
        vol_ort = volume.rolling(10).mean().iloc[-1]

        i = -1

        ema_cross   = float(e5.iloc[i]) > float(e13.iloc[i])
        sar_alti    = not pd.isna(psar.iloc[i]) and float(psar.iloc[i]) < float(close.iloc[i])
        cci_yukari  = float(cci.iloc[i]) > 90
        hacim_artis = float(vol_degisim) > 30
        hacim_yeter = float(vol_ort) > 1_000_000

        guclu = ema_cross and sar_alti and cci_yukari and hacim_artis and hacim_yeter

        if not guclu:
            return None

        fiyat   = round(float(close.iloc[i]), 2)
        degisim = round(float((close.iloc[i] - close.iloc[-2]) / close.iloc[-2] * 100), 2)
        cci_val = round(float(cci.iloc[i]), 0)

        return {"fiyat": fiyat, "degisim": degisim, "cci": cci_val, "vol_degisim": round(vol_degisim, 0)}
    except:
        return None

def tara():
    send_telegram("🔍 <b>BIST Tarama Başlıyor...</b>")

    hisse_listesi = get_all_hisseler()

    al_list = []
    sat_list = []
    ralli_list = []
    bot_list = []
    dip_list = []
    guclu_list = []
    tarandi = 0

    for hisse in hisse_listesi:
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

        gt = get_guclu_trend(hisse)
        if gt:
            deg = f"+{gt['degisim']}%" if gt['degisim'] >= 0 else f"{gt['degisim']}%"
            guclu_list.append(f"<b>{hisse}</b>  {gt['fiyat']}  ({deg})  CCI:{int(gt['cci'])}  Hcm:{int(gt['vol_degisim'])}%")

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
    if guclu_list:
        mesaj += f"💪 <b>GÜÇLÜ TREND ({len(guclu_list)} hisse)</b>\n"
        mesaj += "\n".join([f"• {h}" for h in guclu_list]) + "\n\n"

    if tarandi == 0:
        mesaj = "⚠️ Hiç veri çekilemedi.\n\n"

    mesaj += f"─────────────────────\n✅ {tarandi} hisse tarandı\n⏳ 60 dakika bekleniyor..."

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

def tarama_loop():
    time.sleep(15)
    while True:
        try:
            if seans_acik():
                tara()
            else:
                tz = pytz.timezone("Europe/Istanbul")
                now = datetime.now(tz)
                send_telegram(f"💤 Seans kapalı ({now.strftime('%H:%M')}). Robot beklemede.")
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
