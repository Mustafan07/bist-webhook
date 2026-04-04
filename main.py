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

# Gün içi sinyal hafızası
sinyal_hafiza = {}

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
        df = hisse.history(period="12mo")
        if df is None or len(df) < 60:
            return None
        df = df.dropna()
        if len(df) < 60:
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

        if not (ema_cross and sar_alti and cci_yukari and hacim_artis and hacim_yeter):
            return None

        fiyat   = round(float(close.iloc[i]), 2)
        degisim = round(float((close.iloc[i] - close.iloc[-2]) / close.iloc[-2] * 100), 2)
        cci_val = round(float(cci.iloc[i]), 0)

        return {"fiyat": fiyat, "degisim": degisim, "cci": cci_val, "vol_degisim": round(vol_degisim, 0)}
    except:
        return None

def get_dip_star(ticker):
    try:
        result = get_data(ticker)
        if result is None:
            return None
        close, high, low, volume = result

        rsi = ta.rsi(close, 14)
        macd_df = ta.macd(close, 12, 26, 9)
        macd_hist = macd_df.iloc[:, 2]  # histogram

        # 52 haftalık (250 gün) min
        min_250 = close.rolling(250).min()
        # 20 günlük min
        min_20 = close.rolling(20).min()

        i  = -1
        p  = -2
        p2 = -3

        # Hacim trendi — son 3 gün artıyor mu
        vol_artan = (float(volume.iloc[i]) > float(volume.iloc[p]) and
                     float(volume.iloc[p]) > float(volume.iloc[p2]))

        # Hacim ortalaması
        vol_ort5 = volume.rolling(5).mean()

        # Kriterler
        # 1. Fiyat 52 haftalık dibin %20 içinde
        dip_yakin = float(close.iloc[i]) <= float(min_250.iloc[i]) * 1.20

        # 2. Fiyat 20 günlük dip bölgesinde
        dip_20 = float(close.iloc[i]) <= float(min_20.iloc[i]) * 1.05

        # 3. RSI 35 altından yukarı dönüş
        rsi_donus = float(rsi.iloc[p]) < 35 and float(rsi.iloc[i]) > float(rsi.iloc[p])

        # 4. MACD histogram dipten yukarı dönüş
        macd_donus = (float(macd_hist.iloc[p2]) < float(macd_hist.iloc[p]) and
                      float(macd_hist.iloc[p]) < float(macd_hist.iloc[i]) and
                      float(macd_hist.iloc[i]) < 0)  # hala negatif ama yukarı dönüyor

        # 5. Hacim artışı
        hacim_artis = vol_artan or float(volume.iloc[i]) > float(vol_ort5.iloc[i]) * 1.5

        if not (dip_yakin and rsi_donus and macd_donus and hacim_artis):
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

def gunluk_rapor_gonder():
    global sinyal_hafiza
    if not sinyal_hafiza:
        send_telegram("📊 <b>GÜNLÜK RAPOR</b>\nBugün sinyal çıkmadı.")
        sinyal_hafiza = {}
        return

    sirali = sorted(sinyal_hafiza.items(), key=lambda x: len(x[1]["sinyaller"]), reverse=True)
    guclu = [(h, v) for h, v in sirali if len(v["sinyaller"]) >= 3]
    orta  = [(h, v) for h, v in sirali if len(v["sinyaller"]) == 2]
    tek   = [(h, v) for h, v in sirali if len(v["sinyaller"]) == 1]

    mesaj = "📊 <b>GÜNLÜK SİNYAL RAPORU</b>\n\n"

    if guclu:
        mesaj += "🏆 <b>GÜÇLÜ ADAYLAR (3+ sinyal)</b>\n"
        for h, v in guclu:
            sayac = {}
            for s in v["sinyaller"]:
                sayac[s] = sayac.get(s, 0) + 1
            detay = ", ".join([f"{s}:{c}" for s, c in sayac.items()])
            mesaj += f"• <b>{h}</b>  {v['fiyat']}  — {len(v['sinyaller'])}x ({detay})\n"
        mesaj += "\n"

    if orta:
        mesaj += "⚡ <b>TEKRARLAYAN (2 sinyal)</b>\n"
        for h, v in orta:
            sayac = {}
            for s in v["sinyaller"]:
                sayac[s] = sayac.get(s, 0) + 1
            detay = ", ".join([f"{s}:{c}" for s, c in sayac.items()])
            mesaj += f"• <b>{h}</b>  {v['fiyat']}  — ({detay})\n"
        mesaj += "\n"

    if tek:
        mesaj += "📌 <b>TEK SİNYAL</b>\n"
        for h, v in tek:
            mesaj += f"• <b>{h}</b>  {v['fiyat']}  — {v['sinyaller'][0]}\n"

    mesaj += f"\n─────────────────────\n📅 {len(sinyal_hafiza)} farklı hisse sinyal verdi."

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

    sinyal_hafiza = {}

def dip_star_rapor_gonder():
    send_telegram("🌟 <b>DİP STAR Taraması Başlıyor...</b>")

    dip_list = []
    tarandi = 0

    for hisse in BIST_HISSELER:
        sonuc = get_dip_star(hisse)
        if sonuc is not None:
            tarandi += 1
            deg = f"+{sonuc['degisim']}%" if sonuc['degisim'] >= 0 else f"{sonuc['degisim']}%"
            dip_list.append(f"<b>{hisse}</b>  {sonuc['fiyat']}  ({deg})  RSI:{int(sonuc['rsi'])}")

    mesaj = "🌟🚀 <b>DİP STAR RAPORU</b>\n"
    mesaj += "─────────────────────\n"
    mesaj += "<i>Uzun düşüş sonrası dip dönüş sinyali veren hisseler</i>\n\n"

    if dip_list:
        for h in dip_list:
            mesaj += f"⭐ {h}\n"
    else:
        mesaj += "Bugün DİP STAR kriteri karşılayan hisse bulunamadı.\n"

    mesaj += f"\n─────────────────────\n✅ {tarandi} hisse DİP STAR kriterini karşıladı."

    for i in range(0, len(mesaj), 4000):
        send_telegram(mesaj[i:i+4000])

def tara():
    send_telegram("🔍 <b>BIST Tarama Başlıyor... (566 hisse)</b>")

    al_list = []
    sat_list = []
    ralli_list = []
    bot_list = []
    dip_list = []
    guclu_list = []
    tarandi = 0

    for hisse in BIST_HISSELER:
        sonuc = get_signals(hisse)
        if sonuc:
            tarandi += 1
            deg  = f"+{sonuc['degisim']}%" if sonuc['degisim'] >= 0 else f"{sonuc['degisim']}%"
            bilgi = f"<b>{hisse}</b>  {sonuc['fiyat']}  ({deg})  RSI:{int(sonuc['rsi'])}"
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

        gt = get_guclu_trend(hisse)
        if gt:
            deg = f"+{gt['degisim']}%" if gt['degisim'] >= 0 else f"{gt['degisim']}%"
            guclu_list.append(f"<b>{hisse}</b>  {gt['fiyat']}  ({deg})  CCI:{int(gt['cci'])}  Hcm:{int(gt['vol_degisim'])}%")
            hafizaya_ekle(hisse, "GÜÇLÜ TREND", gt['fiyat'])

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
    rapor_gonderildi = False
    dip_star_gonderildi = False

    while True:
        try:
            tz = pytz.timezone("Europe/Istanbul")
            now = datetime.now(tz)

            # Günlük rapor 17:30'da
            if now.weekday() < 5 and now.hour == 17 and not rapor_gonderildi:
                gunluk_rapor_gonder()
                rapor_gonderildi = True

            # DİP STAR raporu 18:30'da
            if now.weekday() < 5 and now.hour == 18 and now.minute >= 30 and not dip_star_gonderildi:
                dip_star_rapor_gonder()
                dip_star_gonderildi = True

            # Gece yarısı bayrakları sıfırla
            if now.hour == 0:
                rapor_gonderildi = False
                dip_star_gonderildi = False

            if seans_acik():
                tara()
            else:
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
