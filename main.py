import os
os.environ["NUMBA_DISABLE_JIT"] = "1"

VERSION = "2026-05-15"
print(f"BOT BAŞLADI - Versiyon: {VERSION}")

from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta
import borsapy as bp
import threading
import time
import json
import random
import string
import websocket
from datetime import datetime
import pytz

app = Flask(__name__)

TELEGRAM_TOKEN = "8760124700:AAE3BqqIwXZ4xNVkdaDdtpdBEo7WYZg4lvY"
CHAT_ID = "635329910"

sinyal_hafiza = {}

# Canlı izleme için global liste
canli_izleme = {}        # {"THYAO": {"giris": 311.0, "son": 311.0}, ...}
canli_izleme_lock = threading.Lock()
ws_app = None
ws_session = None

BIST_HISSELER = [
    "A1CAP","A1YEN","ACSEL","ADEL","ADESE","ADGYO","AEFES","AFYON","AGESA","AGHOL",
    "AGROT","AGYO","AHGAZ","AHSGY","AKBNK","AKCNS","AKENR","AKFGY","AKFIS","AKFYE",
    "AKGRT","AKHAN","AKMGY","AKSA","AKSEN","AKSGY","AKSUE","AKYHO","ALARK","ALBRK",
    "ALCAR","ALCTL","ALFAS","ALGYO","ALKA","ALKIM","ALKLC","ALTNY","ALVES","ANELE",
    "ANGEN","ANHYT","ANSGR","ARASE","ARCLK","ARDYZ","ARENA","ARFYE","ARMGD","ARSAN",
    "ARTMS","ARZUM","ASELS","ASGYO","ASTOR","ASUZU","ATAGY","ATAKP","ATATP","ATATR",
    "AVGYO","AVHOL","AVOD","AVPGY","AVTUR","AYCES","AYDEM","AYEN","AYGAZ","AZTEK",
    "BAGFS","BAHKM","BAKAB","BALSU","BANVT","BARMA","BASGZ","BAYRK","BEGYO","BERA",
    "BESLR","BESTE","BEYAZ","BFREN","BIENY","BIGCH","BIGEN","BIGTK","BIMAS","BINBN",
    "BINHO","BIOEN","BIZIM","BJKAS","BLCYT","BLUME","BMSCH","BMSTL","BNTAS","BOBET",
    "BORLS","BORSK","BOSSA","BRISA","BRKSN","BRKVY","BRLSM","BRSAN","BRYAT","BSOKE",
    "BTCIM","BUCIM","BULGS","BURCE","BURVA","BVSAN","BYDNR","CANTE","CATES","CCOLA",
    "CELHA","CEMAS","CEMTS","CEMZY","CEOEM","CGCAM","CIMSA","CLEBI","CMBTN","CONSE",
    "COSMO","CRDFA","CRFSA","CUSAN","CVKMD","CWENE","DAGI","DAPGM","DARDL","DCTTR",
    "DENGE","DERHL","DERIM","DESA","DESPC","DEVA","DGATE","DGGYO","DGNMO","DITAS",
    "DMRGD","DMSAS","DNISI","DOAS","DOCO","DOFER","DOFRB","DOGUB","DOHOL","DOKTA",
    "DSTKF","DUNYH","DURDO","DURKN","DYOBY","DZGYO","EBEBK","ECILC","ECOGR","ECZYT",
    "EDATA","EDIP","EFOR","EGEEN","EGEGY","EGEPO","EGGUB","EGPRO","EGSER","EKGYO",
    "EKOS","EKSUN","ELITE","EMKEL","EMPAE","ENDAE","ENERY","ENJSA","ENKAI","ENSRI",
    "ENTRA","EPLAS","ERBOS","ERCB","EREGL","ERSU","ESCAR","ESCOM","ESEN","ETILR",
    "EUPWR","EUREN","EYGYO","FADE","FENER","FLAP","FMIZP","FONET","FORMT","FORTE",
    "FRIGO","FRMPL","FROTO","FZLGY","GARAN","GARFA","GEDIK","GEDZA","GENIL","GENKM",
    "GENTS","GEREL","GESAN","GIPTA","GLBMD","GLCVY","GLRMK","GLRYH","GLYHO","GMTAS",
    "GOKNR","GOLTS","GOODY","GOZDE","GRSEL","GRTHO","GSDDE","GSDHO","GSRAY","GUBRF",
    "GUNDG","GWIND","GZNMI","HALKB","HATEK","HATSN","HDFGS","HEDEF","HEKTS","HKTM",
    "HLGYO","HOROZ","HRKET","HTTBT","HUBVC","HUNER","HURGZ","ICBCT","ICUGS","IDGYO",
    "IEYHO","IHAAS","IHEVA","IHGZT","IHLAS","IHLGM","IHYAY","IMASM","INDES","INFO",
    "INGRM","INTEM","INVEO","INVES","ISATR","ISBTR","ISCTR","ISDMR","ISFIN","ISGSY",
    "ISGYO","ISKPL","ISMEN","ISSEN","IZENR","IZFAS","IZINV","IZMDC","JANTS","KAPLM",
    "KAREL","KARSN","KARTN","KATMR","KAYSE","KBORU","KCAER","KCHOL","KFEIN","KGYO",
    "KIMMR","KLGYO","KLKIM","KLMSN","KLRHO","KLSER","KLSYN","KLYPV","KMPUR","KNFRT",
    "KOCMT","KONKA","KONTR","KONYA","KOPOL","KORDS","KOTON","KRDMA","KRDMB","KRDMD",
    "KRGYO","KRONT","KRPLS","KRSTL","KRTEK","KRVGD","KTLEV","KTSKR","KUTPO","KUVVA",
    "KUYAS","KZBGY","KZGYO","LIDER","LIDFA","LILAK","LINK","LKMNH","LMKDC","LOGO",
    "LRSHO","LUKSK","LXGYO","LYDHO","LYDYE","MAALT","MACKO","MAGEN","MAKIM","MAKTK",
    "MANAS","MARBL","MARKA","MARMR","MARTI","MAVI","MCARD","MEDTR","MEGMT","MEKAG",
    "MEPET","MERCN","MERIT","MERKO","METRO","MEYSU","MGROS","MHRGY","MIATK","MNDRS",
    "MNDTR","MOBTL","MOGAN","MOPAS","MPARK","MRGYO","MRSHL","MSGYO","MTRKS","MZHLD",
    "NATEN","NETAS","NETCD","NIBAS","NTGAZ","NTHOL","NUGYO","NUHCM","OBAMS","OBASE",
    "ODAS","ODINE","OFSYM","ONCSM","ONRYT","ORCAY","ORGE","OSMEN","OSTIM","OTKAR",
    "OTTO","OYAKC","OYLUM","OYYAT","OZATD","OZGYO","OZKGY","OZRDN","OZSUB","OZYSR",
    "PAGYO","PAHOL","PAMEL","PAPIL","PARSN","PASEU","PATEK","PCILT","PEKGY","PENGD",
    "PENTA","PETKM","PETUN","PGSUS","PINSU","PKART","PKENT","PLTUR","PNLSN","PNSUT",
    "POLHO","POLTK","PRDGS","PRKAB","PRKME","PRZMA","PSDTC","PSGYO","QUAGR","RALYH",
    "RAYSG","REEDR","RGYAS","RNPOL","RODRG","RTALB","RUBNS","RUZYE","RYGYO","RYSAS",
    "SAFKR","SAHOL","SAMAT","SANEL","SANFM","SANKO","SARKY","SASA","SAYAS","SDTTR",
    "SEGMN","SEGYO","SEKFK","SEKUR","SELEC","SELVA","SERNT","SEYKM","SILVR","SISE",
    "SKBNK","SKTAS","SKYLP","SKYMD","SMART","SMRTG","SMRVA","SNGYO","SNICA","SOKE",
    "SOKM","SONME","SRVGY","SUNTK","SURGY","SUWEN","SVGYO","TABGD","TARKM","TATEN",
    "TATGD","TAVHL","TBORG","TCELL","TCKRC","TDGYO","TEHOL","TEKTU","TERA","TEZOL",
    "TGSAS","THYAO","TKFEN","TKNSA","TLMAN","TMPOL","TMSN","TNZTP","TOASO","TRALT",
    "TRCAS","TRENJ","TRGYO","TRHOL","TRILC","TRMET","TSGYO","TSKB","TSPOR","TTKOM",
    "TTRAK","TUCLK","TUKAS","TUPRS","TUREX","TURGG","TURSG","UCAYM","UFUK","ULAS",
    "ULKER","ULUFA","ULUSE","ULUUN","UNLU","USAK","VAKBN","VAKFA","VAKFN","VAKKO",
    "VANGD","VBTYZ","VERTU","VERUS","VESBE","VESTL","VKGYO","VKING","VRGYO","VSNMD",
    "YAPRK","YATAS","YAYLA","YEOTK","YESIL","YGGYO","YIGIT","YKBNK","YKSLN","YUNSA",
    "YYLGD","ZEDUR","ZERGY","ZGYO","ZOREN","ZRGYO"
]

# ── WEBSOCKET CANLI İZLEME ─────────────────────────────────

def ws_wrap(msg):
    return f"~m~{len(msg)}~m~{msg}"

def ws_build(method, params):
    return ws_wrap(json.dumps({"m": method, "p": params}))

def ws_gen_session():
    return "qs_" + "".join(random.choices(string.ascii_lowercase, k=12))

def ws_parse(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    pos, out = 0, []
    while pos < len(raw):
        if not raw[pos:].startswith("~m~"):
            pos += 1
            continue
        pos += 3
        end = raw.find("~m~", pos)
        if end == -1:
            break
        length = int(raw[pos:end])
        pos = end + 3
        out.append(raw[pos:pos + length])
        pos += length
    return out

def ws_on_open(ws):
    global ws_session
    ws_session = ws_gen_session()
    ws.send(ws_build("set_auth_token", ["unauthorized_user_token"]))
    ws.send(ws_build("quote_create_session", [ws_session]))
    ws.send(ws_build("quote_set_fields", [ws_session, "lp", "chp", "volume"]))
    with canli_izleme_lock:
        semboller = [f"BIST:{h}" for h in canli_izleme.keys()]
    if semboller:
        ws.send(ws_build("quote_add_symbols", [ws_session, *semboller]))

def ws_on_message(ws, raw):
    for content in ws_parse(raw):
        if content.startswith("~h~"):
            ws.send(ws_wrap(content))
            continue
        try:
            msg = json.loads(content)
        except:
            continue
        if msg.get("m") == "qsd":
            data = msg["p"][1]
            symbol = data.get("n", "").replace("BIST:", "")
            v = data.get("v", {})
            if "lp" in v and symbol:
                fiyat = float(v["lp"])
                chp = float(v.get("chp", 0))
                vol = int(v.get("volume", 0))
                canli_fiyat_kontrol(symbol, fiyat, chp, vol)

def ws_on_error(ws, error):
    pass

def ws_on_close(ws, *args):
    pass

def canli_fiyat_kontrol(hisse, fiyat, chp, vol):
    with canli_izleme_lock:
        if hisse not in canli_izleme:
            return
        bilgi = canli_izleme[hisse]
        giris = bilgi.get("giris", fiyat)
        son_bildirim = bilgi.get("son_bildirim", 0)
        bilgi["son"] = fiyat

    degisim = round((fiyat - giris) / giris * 100, 2) if giris > 0 else 0

    # Her %2 harekette bildir, aynı yönde max 1 bildirim / 30 dk
    simdi = time.time()
    if abs(degisim) >= 2.0 and (simdi - son_bildirim) > 1800:
        emoji = "🚀" if degisim > 0 else "🔻"
        mesaj = (f"{emoji} <b>CANLI İZLEME: {hisse}</b>\n"
                 f"💰 Fiyat: {fiyat}\n"
                 f"📊 Giriş'ten: {'+' if degisim>=0 else ''}{degisim}%\n"
                 f"📈 Günlük: {'+' if chp>=0 else ''}{chp}%\n"
                 f"🔢 Hacim: {vol:,}")
        send_telegram(mesaj)
        with canli_izleme_lock:
            canli_izleme[hisse]["son_bildirim"] = simdi

def canli_izleme_baslat(hisse_listesi):
    """DİP STAR hisselerini WebSocket ile izlemeye al."""
    global ws_app, canli_izleme

    with canli_izleme_lock:
        canli_izleme = {}
        for h in hisse_listesi:
            canli_izleme[h] = {"giris": 0, "son": 0, "son_bildirim": 0}

    if not hisse_listesi:
        return

    sembol_str = ", ".join(hisse_listesi)
    send_telegram(f"👁 <b>CANLI İZLEME BAŞLADI</b>\n{sembol_str}")

    def ws_thread():
        global ws_app
        while True:
            try:
                ws_app = websocket.WebSocketApp(
                    "wss://data.tradingview.com/socket.io/websocket?type=chart",
                    on_open=ws_on_open,
                    on_message=ws_on_message,
                    on_error=ws_on_error,
                    on_close=ws_on_close,
                    header={"Origin": "https://www.tradingview.com"},
                )
                ws_app.run_forever(ping_interval=0, skip_utf8_validation=True)
            except:
                pass
            time.sleep(30)  # bağlantı kopunca 30 sn bekle yeniden bağlan

    t = threading.Thread(target=ws_thread, daemon=True)
    t.start()

def canli_izleme_durdur():
    global ws_app, canli_izleme
    with canli_izleme_lock:
        canli_izleme = {}
    if ws_app:
        try:
            ws_app.close()
        except:
            pass

# ──────────────────────────────────────────────────────────

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
        open_  = pd.Series(df["Open"].values, dtype=float)
        return close, high, low, volume, open_
    except:
        return None

def get_signals(ticker, data=None):
    try:
        result = data if data else get_data(ticker)
        if result is None:
            return None
        close, high, low, volume, open_ = result

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

def get_guclu_trend(ticker, data=None):
    try:
        result = data if data else get_data(ticker)
        if result is None:
            return None
        close, high, low, volume, open_ = result

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

        if not (ema_cross and sar_alti and cci_yukari and hacim_artis and hacim_yeter):
            return None

        fiyat   = round(float(close.iloc[i]), 2)
        degisim = round(float((close.iloc[i] - close.iloc[-2]) / close.iloc[-2] * 100), 2)
        cci_val = round(float(cci.iloc[i]), 0)

        return {"fiyat": fiyat, "degisim": degisim, "cci": cci_val, "vol_degisim": round(vol_degisim, 0)}
    except:
        return None

def bullish_engulfing(open_, close, i=-1, p=-2):
    onceki_kirmizi = float(close.iloc[p]) < float(open_.iloc[p])
    bugunki_yesil  = float(close.iloc[i]) > float(open_.iloc[i])
    yutuyor = (float(open_.iloc[i]) <= float(close.iloc[p]) and
               float(close.iloc[i]) >= float(open_.iloc[p]))
    return onceki_kirmizi and bugunki_yesil and yutuyor

def get_dip_star(ticker, data=None):
    try:
        result = data if data else get_data(ticker)
        if result is None:
            return None
        close, high, low, volume, open_ = result

        rsi = ta.rsi(close, 14)
        macd_df = ta.macd(close, 12, 26, 9)
        macd_hist = macd_df.iloc[:, 2]
        min_250 = close.rolling(len(close)).min()
        vol_ort5 = volume.rolling(5).mean()

        i  = -1
        p  = -2
        p2 = -3

        puan = 0
        puan_detay = []

        if float(close.iloc[i]) <= float(min_250.iloc[i]) * 1.20:
            puan += 1
            puan_detay.append("Dip")

        if float(rsi.iloc[p]) < 40 and float(rsi.iloc[i]) > float(rsi.iloc[p]):
            puan += 1
            puan_detay.append("RSI↑")

        if (float(macd_hist.iloc[p2]) < float(macd_hist.iloc[p]) and
                float(macd_hist.iloc[p]) < float(macd_hist.iloc[i]) and
                float(macd_hist.iloc[i]) < 0):
            puan += 1
            puan_detay.append("MACD↑")

        if float(volume.iloc[i]) > float(vol_ort5.iloc[i]) * 1.2:
            puan += 1
            puan_detay.append("Hacim↑")

        if bullish_engulfing(open_, close):
            puan += 1
            puan_detay.append("Engulf")

        if puan < 3:
            return None

        fiyat   = round(float(close.iloc[i]), 2)
        degisim = round(float((close.iloc[i] - close.iloc[p]) / close.iloc[p] * 100), 2)
        rsi_val = round(float(rsi.iloc[i]), 0)

        return {"fiyat": fiyat, "degisim": degisim, "rsi": rsi_val,
                "puan": puan, "detay": "+".join(puan_detay)}
    except:
        return None

def get_kirilim(ticker, data=None):
    try:
        result = data if data else get_data(ticker)
        if result is None:
            return None
        close, high, low, volume, open_ = result

        e20  = ta.ema(close, 20)
        e50  = ta.ema(close, 50)
        e200 = ta.ema(close, 200)
        atr = ta.atr(high, low, close, 14)
        atr_sma = atr.rolling(20).mean()
        rsi = ta.rsi(close, 14)
        vol_sma20 = volume.rolling(20).mean()
        highest_20 = high.rolling(20).max()
        lowest_10  = low.rolling(10).min()
        lowest_20  = low.rolling(20).min()

        i = -1
        p = -2

        trend = (float(e20.iloc[i]) > float(e50.iloc[i]) and
                 float(e50.iloc[i]) > float(e200.iloc[i]) and
                 float(close.iloc[i]) > float(e20.iloc[i]) and
                 float(close.iloc[i]) > float(e50.iloc[i]))

        yukselen_dip  = float(lowest_10.iloc[i]) > float(lowest_20.iloc[i])
        dusuk_vol     = float(atr.iloc[i]) < float(atr_sma.iloc[i])
        rsi_guclu     = float(rsi.iloc[i]) > 52 and float(rsi.iloc[i]) > float(rsi.iloc[p])
        hacim_artiyor = float(volume.iloc[i]) > float(vol_sma20.iloc[i]) * 1.15
        zirve_yakin   = (float(close.iloc[i]) >= float(highest_20.iloc[i]) * 0.96 and
                         float(close.iloc[i]) < float(highest_20.iloc[i]) * 1.02)

        if not (trend and yukselen_dip and dusuk_vol and rsi_guclu and hacim_artiyor and zirve_yakin):
            return None

        fiyat   = round(float(close.iloc[i]), 2)
        degisim = round(float((close.iloc[i] - close.iloc[p]) / close.iloc[p] * 100), 2)
        rsi_val = round(float(rsi.iloc[i]), 0)

        return {"fiyat": fiyat, "degisim": degisim, "rsi": rsi_val}
    except:
        return None

def hafizaya_ekle(hisse, sinyal_turu, fiyat):
    global sinyal_hafiza
    if hisse not in sinyal_hafiza:
        sinyal_hafiza[hisse] = {"sinyaller": [], "fiyat": fiyat}
    sinyal_hafiza[hisse]["sinyaller"].append(sinyal_turu)
    sinyal_hafiza[hisse]["fiyat"] = fiyat

def birikim_raporu_gonder():
    tz = pytz.timezone("Europe/Istanbul")
    now = datetime.now(tz)
    saat = now.strftime("%H:%M")
    bitis = now.replace(hour=18, minute=30, second=0, microsecond=0)
    kalan = bitis - now
    kalan_saat = max(0, int(kalan.total_seconds() // 3600))
    kalan_dk = max(0, int((kalan.total_seconds() % 3600) // 60))

    if not sinyal_hafiza:
        return

    AL_SINYALLER = {"AL", "RALLİ", "BOT AL", "RSI DİP", "KIRILIM", "GÜÇLÜ TREND", "DİP STAR"}

    al_grup  = {h: v for h, v in sinyal_hafiza.items()
                if any(s in AL_SINYALLER for s in v["sinyaller"])
                and not any(s == "SAT" for s in v["sinyaller"])}
    sat_grup = {h: v for h, v in sinyal_hafiza.items()
                if any(s == "SAT" for s in v["sinyaller"])
                and not any(s in AL_SINYALLER for s in v["sinyaller"])}

    mesaj = f"📊 <b>GÜNLÜK BİRİKİM ({saat})</b>\n"
    mesaj += f"⏰ Seans kapanışına {kalan_saat}s {kalan_dk}dk kaldı\n"
    mesaj += "─────────────────────\n\n"

    if al_grup:
        mesaj += "🟢 <b>AL GRUBU</b>\n"
        al_sirali = sorted(al_grup.items(), key=lambda x: len(x[1]["sinyaller"]), reverse=True)
        guclu_al = [(h, v) for h, v in al_sirali if len(v["sinyaller"]) >= 3]
        orta_al  = [(h, v) for h, v in al_sirali if len(v["sinyaller"]) == 2]
        tek_al   = [(h, v) for h, v in al_sirali if len(v["sinyaller"]) == 1]

        if guclu_al:
            mesaj += "🏆 "
            parcalar = []
            for h, v in guclu_al:
                sayac = {}
                for s in v["sinyaller"]:
                    sayac[s] = sayac.get(s, 0) + 1
                detay = "+".join([f"{s}:{c}" for s, c in sayac.items() if s in AL_SINYALLER])
                parcalar.append(f"<b>{h}</b> {len(v['sinyaller'])}x({detay})")
            mesaj += " | ".join(parcalar) + "\n"
        if orta_al:
            mesaj += "⚡ " + " | ".join([f"<b>{h}</b> 2x" for h, v in orta_al]) + "\n"
        if tek_al:
            mesaj += "📌 " + " | ".join([f"<b>{h}</b>" for h, v in tek_al]) + "\n"
        mesaj += "\n"

    if sat_grup:
        mesaj += "🔴 <b>SAT GRUBU</b>\n"
        sat_sirali = sorted(sat_grup.items(), key=lambda x: len(x[1]["sinyaller"]), reverse=True)
        guclu_sat = [(h, v) for h, v in sat_sirali if len(v["sinyaller"]) >= 3]
        orta_sat  = [(h, v) for h, v in sat_sirali if len(v["sinyaller"]) == 2]
        tek_sat   = [(h, v) for h, v in sat_sirali if len(v["sinyaller"]) == 1]

        if guclu_sat:
            mesaj += "🏆 " + " | ".join([f"<b>{h}</b> {len(v['sinyaller'])}x" for h, v in guclu_sat]) + "\n"
        if orta_sat:
            mesaj += "⚡ " + " | ".join([f"<b>{h}</b> 2x" for h, v in orta_sat]) + "\n"
        if tek_sat:
            mesaj += "📌 " + " | ".join([f"<b>{h}</b>" for h, v in tek_sat]) + "\n"

    mesaj += f"\n─────────────────────\n📅 {len(sinyal_hafiza)} hisse sinyal verdi"

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

def gunluk_rapor_gonder():
    global sinyal_hafiza
    if not sinyal_hafiza:
        send_telegram("📊 <b>GÜNLÜK RAPOR</b>\nBugün sinyal çıkmadı.")
        sinyal_hafiza = {}
        return

    AL_SINYALLER = {"AL", "RALLİ", "BOT AL", "RSI DİP", "KIRILIM", "GÜÇLÜ TREND", "DİP STAR"}
    temiz_al  = {}
    temiz_sat = {}
    cakisan   = {}

    for hisse, v in sinyal_hafiza.items():
        al_sayisi  = sum(1 for s in v["sinyaller"] if s in AL_SINYALLER)
        sat_sayisi = sum(1 for s in v["sinyaller"] if s == "SAT")
        if al_sayisi > 0 and sat_sayisi > 0:
            cakisan[hisse] = v
        elif al_sayisi > 0:
            temiz_al[hisse] = v
        elif sat_sayisi > 0:
            temiz_sat[hisse] = v

    mesaj = "📊 <b>GÜNLÜK SİNYAL RAPORU</b>\n\n"

    if temiz_al:
        mesaj += "🟢 <b>AL GRUBU</b>\n"
        sirali = sorted(temiz_al.items(), key=lambda x: len(x[1]["sinyaller"]), reverse=True)
        guclu = [(h, v) for h, v in sirali if len(v["sinyaller"]) >= 3]
        orta  = [(h, v) for h, v in sirali if len(v["sinyaller"]) == 2]
        tek   = [(h, v) for h, v in sirali if len(v["sinyaller"]) == 1]
        if guclu:
            mesaj += "🏆 <b>Güçlü (3+)</b>\n"
            for h, v in guclu:
                sayac = {}
                for s in v["sinyaller"]:
                    sayac[s] = sayac.get(s, 0) + 1
                detay = ", ".join([f"{s}:{c}" for s, c in sayac.items()])
                mesaj += f"• <b>{h}</b>  {v['fiyat']}  {len(v['sinyaller'])}x ({detay})\n"
            mesaj += "\n"
        if orta:
            mesaj += "⚡ <b>Tekrarlayan (2)</b>\n"
            for h, v in orta:
                sayac = {}
                for s in v["sinyaller"]:
                    sayac[s] = sayac.get(s, 0) + 1
                detay = ", ".join([f"{s}:{c}" for s, c in sayac.items()])
                mesaj += f"• <b>{h}</b>  {v['fiyat']}  ({detay})\n"
            mesaj += "\n"
        if tek:
            mesaj += "📌 <b>Tek sinyal</b>\n"
            mesaj += "  ".join([f"<b>{h}</b>" for h, v in tek]) + "\n"
        mesaj += "\n"

    if temiz_sat:
        mesaj += "🔴 <b>SAT GRUBU</b>\n"
        sirali = sorted(temiz_sat.items(), key=lambda x: len(x[1]["sinyaller"]), reverse=True)
        guclu = [(h, v) for h, v in sirali if len(v["sinyaller"]) >= 3]
        orta  = [(h, v) for h, v in sirali if len(v["sinyaller"]) == 2]
        tek   = [(h, v) for h, v in sirali if len(v["sinyaller"]) == 1]
        if guclu:
            mesaj += "🏆 <b>Güçlü (3+)</b>\n"
            for h, v in guclu:
                mesaj += f"• <b>{h}</b>  {v['fiyat']}  {len(v['sinyaller'])}x SAT\n"
            mesaj += "\n"
        if orta:
            mesaj += "⚡ <b>Tekrarlayan (2)</b>\n"
            for h, v in orta:
                mesaj += f"• <b>{h}</b>  {v['fiyat']}\n"
            mesaj += "\n"
        if tek:
            mesaj += "📌 <b>Tek sinyal</b>\n"
            mesaj += "  ".join([f"<b>{h}</b>" for h, v in tek]) + "\n"
        mesaj += "\n"

    if cakisan:
        mesaj += "⚠️ <b>ÇAKIŞAN SİNYAL (bekle)</b>\n"
        sirali = sorted(cakisan.items(), key=lambda x: len(x[1]["sinyaller"]), reverse=True)
        for h, v in sirali[:10]:
            sayac = {}
            for s in v["sinyaller"]:
                sayac[s] = sayac.get(s, 0) + 1
            detay = ", ".join([f"{s}:{c}" for s, c in sayac.items()])
            mesaj += f"• <b>{h}</b>  {v['fiyat']}  ({detay})\n"
        mesaj += "\n"

    mesaj += f"─────────────────────\n"
    mesaj += f"📅 {len(temiz_al)} AL | {len(temiz_sat)} SAT | {len(cakisan)} Çakışan"

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

    sinyal_hafiza = {}

def dip_star_rapor_gonder():
    send_telegram("🌟 <b>DİP STAR Sabah Taraması Başlıyor...</b>")
    dip_list_5 = []
    dip_list_4 = []
    dip_list_3 = []
    canli_liste = []  # 4/5 ve 5/5 hisseler canlı izlemeye alınacak

    for hisse in BIST_HISSELER:
        data = get_data(hisse)
        sonuc = get_dip_star(hisse, data)
        if sonuc is not None:
            deg = f"+{sonuc['degisim']}%" if sonuc['degisim'] >= 0 else f"{sonuc['degisim']}%"
            satir = f"<b>{hisse}</b>  {sonuc['fiyat']}  ({deg})  RSI:{int(sonuc['rsi'])}  [{sonuc['detay']}]"
            if sonuc["puan"] == 5:
                dip_list_5.append(satir)
                canli_liste.append(hisse)
            elif sonuc["puan"] == 4:
                dip_list_4.append(satir)
                canli_liste.append(hisse)
            else:
                dip_list_3.append(satir)

    mesaj = "🌟🚀 <b>DİP STAR RAPORU</b>\n"
    mesaj += "<i>Bir önceki günün kapanışına göre — bugün aksiyon al!</i>\n"
    mesaj += "─────────────────────\n\n"

    if dip_list_5:
        mesaj += "🌟🌟🌟 <b>MÜKEMMEL (5/5)</b>\n"
        for h in dip_list_5:
            mesaj += f"⭐ {h}\n"
        mesaj += "\n"
    if dip_list_4:
        mesaj += "🌟🌟 <b>GÜÇLÜ (4/5)</b>\n"
        for h in dip_list_4:
            mesaj += f"⭐ {h}\n"
        mesaj += "\n"
    if dip_list_3:
        mesaj += "🌟 <b>OLASI (3/5)</b>\n"
        for h in dip_list_3:
            mesaj += f"⭐ {h}\n"
        mesaj += "\n"

    if not dip_list_5 and not dip_list_4 and not dip_list_3:
        mesaj += "Bugün DİP STAR kriteri karşılayan hisse bulunamadı.\n"

    toplam = len(dip_list_5) + len(dip_list_4) + len(dip_list_3)
    mesaj += f"─────────────────────\n✅ {toplam} hisse DİP STAR kriterini karşıladı."

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

    # 4/5 ve 5/5 hisseleri canlı izlemeye al
    if canli_liste:
        canli_izleme_baslat(canli_liste)

def tara():
    send_telegram(f"🔍 <b>BIST Tarama Başlıyor... (566 hisse) v{VERSION}</b>")

    try:
        test = get_data("THYAO")
        if test is None:
            send_telegram("⚠️ VERİ HATASI: borsapy veri çekemiyor!")
            return
    except Exception as e:
        send_telegram(f"⚠️ VERİ HATASI: {str(e)}")
        return

    al_list = []
    sat_list = []
    ralli_list = []
    bot_list = []
    dip_list = []
    guclu_list = []
    kirilim_list = []
    dip_star_list = []
    tarandi = 0

    for hisse in BIST_HISSELER:
        data = get_data(hisse)
        if data is None:
            continue
        tarandi += 1

        sonuc = get_signals(hisse, data)
        if sonuc:
            bilgi = f"<b>{hisse}</b>  {sonuc['fiyat']}  ({'+' if sonuc['degisim']>=0 else ''}{sonuc['degisim']}%)  RSI:{int(sonuc['rsi'])}"
            if sonuc["ralli"]:
                ralli_list.append(bilgi)
                hafizaya_ekle(hisse, "RALLİ", sonuc['fiyat'])
            elif sonuc["al"]:
                al_list.append(bilgi)
                hafizaya_ekle(hisse, "AL", sonuc['fiyat'])
            if sonuc["sat"]:
                sat_list.append(bilgi)
                hafizaya_ekle(hisse, "SAT", sonuc['fiyat'])
            if sonuc["bot"]:
                bot_list.append(bilgi)
                hafizaya_ekle(hisse, "BOT AL", sonuc['fiyat'])
            if sonuc["dip"]:
                dip_list.append(bilgi)
                hafizaya_ekle(hisse, "RSI DİP", sonuc['fiyat'])

        gt = get_guclu_trend(hisse, data)
        if gt:
            deg_str = f"+{gt['degisim']}%" if gt['degisim'] >= 0 else f"{gt['degisim']}%"
            guclu_list.append(f"<b>{hisse}</b>  {gt['fiyat']}  ({deg_str})  CCI:{int(gt['cci'])}  Hcm:{int(gt['vol_degisim'])}%")
            hafizaya_ekle(hisse, "GÜÇLÜ TREND", gt['fiyat'])

        kr = get_kirilim(hisse, data)
        if kr:
            deg_str = f"+{kr['degisim']}%" if kr['degisim'] >= 0 else f"{kr['degisim']}%"
            kirilim_list.append(f"<b>{hisse}</b>  {kr['fiyat']}  ({deg_str})  RSI:{int(kr['rsi'])}")
            hafizaya_ekle(hisse, "KIRILIM", kr['fiyat'])

        ds = get_dip_star(hisse, data)
        if ds and ds["puan"] >= 4:
            deg_str = f"+{ds['degisim']}%" if ds['degisim'] >= 0 else f"{ds['degisim']}%"
            yildiz = "🌟🌟🌟" if ds["puan"] == 5 else "🌟🌟"
            dip_star_list.append(f"{yildiz} <b>{hisse}</b>  {ds['fiyat']}  ({deg_str})  RSI:{int(ds['rsi'])}  [{ds['detay']}]")
            hafizaya_ekle(hisse, "DİP STAR", ds['fiyat'])

    mesaj = ""
    if al_list:
        mesaj += f"✅ <b>AL ({len(al_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in al_list]) + "\n\n"
    if ralli_list:
        mesaj += f"🚀 <b>RALLİ ({len(ralli_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in ralli_list]) + "\n\n"
    if sat_list:
        mesaj += f"🔴 <b>SAT ({len(sat_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in sat_list]) + "\n\n"
    if bot_list:
        mesaj += f"⬆️ <b>BOT AL ({len(bot_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in bot_list]) + "\n\n"
    if dip_list:
        mesaj += f"🎯 <b>RSI DİP ({len(dip_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in dip_list]) + "\n\n"
    if guclu_list:
        mesaj += f"💪 <b>GÜÇLÜ TREND ({len(guclu_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in guclu_list]) + "\n\n"
    if kirilim_list:
        mesaj += f"🔥 <b>KIRILIM ({len(kirilim_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in kirilim_list]) + "\n\n"
    if dip_star_list:
        mesaj += f"🌟 <b>DİP STAR ({len(dip_star_list)} hisse)</b>\n" + "\n".join([f"• {h}" for h in dip_star_list]) + "\n\n"

    if tarandi == 0:
        mesaj = "⚠️ Hiç veri çekilemedi.\n\n"

    mesaj += f"─────────────────────\n✅ {tarandi} hisse tarandı\n⏳ 60 dakika bekleniyor..."

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

    birikim_raporu_gonder()

def tarama_loop():
    time.sleep(300)
    rapor_gonderildi = False
    dip_star_gonderildi = False
    son_tarama_saati = -1

    while True:
        try:
            tz = pytz.timezone("Europe/Istanbul")
            now = datetime.now(tz)

            if now.hour == 0 and now.minute < 10:
                rapor_gonderildi = False
                dip_star_gonderildi = False
                son_tarama_saati = -1
                canli_izleme_durdur()

            if now.weekday() < 5 and now.hour == 9 and now.minute >= 30 and not dip_star_gonderildi:
                dip_star_rapor_gonder()
                dip_star_gonderildi = True

            if seans_acik():
                if now.hour != son_tarama_saati:
                    son_tarama_saati = now.hour
                    tara()
                    now = datetime.now(tz)
                    if now.weekday() < 5 and now.hour >= 17 and not rapor_gonderildi:
                        gunluk_rapor_gonder()
                        rapor_gonderildi = True

            # Seans kapandıysa WebSocket'i durdur
            if not seans_acik():
                canli_izleme_durdur()

        except Exception as e:
            send_telegram(f"⚠️ Hata: {str(e)}")

        time.sleep(600)

# ── WATCHDOG ──────────────────────────────────────────────
def watchdog(thread_ref):
    while True:
        time.sleep(900)
        if not thread_ref[0].is_alive():
            send_telegram("⚠️ <b>WATCHDOG:</b> Tarama thread öldü! Yeniden başlatılıyor...")
            yeni = threading.Thread(target=tarama_loop, daemon=True)
            yeni.start()
            thread_ref[0] = yeni
# ──────────────────────────────────────────────────────────

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
    tarama_thread = threading.Thread(target=tarama_loop, daemon=True)
    tarama_thread.start()

    thread_ref = [tarama_thread]
    w = threading.Thread(target=watchdog, args=(thread_ref,), daemon=True)
    w.start()

    app.run(host="0.0.0.0", port=8080)
