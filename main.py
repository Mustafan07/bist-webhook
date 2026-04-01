from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = "8760124700:AAG1UG8FpfETC3wBhvleqMaIpXi8FUvek8A"
CHAT_ID = "635329910"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return "ok", 200
    sinyal = data.get("sinyal", "")
    hisse = data.get("hisse", "")
    fiyat = data.get("fiyat", "")
    tf = data.get("tf", "")
    if sinyal == "AL":
        emoji = "✅"
    elif sinyal == "SAT":
        emoji = "🔴"
    elif sinyal == "RALLI":
        emoji = "🚀"
    elif sinyal == "BOT_AL":
        emoji = "⬆️"
    else:
        emoji = "📊"
    mesaj = f"{emoji} <b>{sinyal}</b>\n📈 Hisse: <b>{hisse}</b>\n💰 Fiyat: {fiyat}\n⏱ TF: {tf}"
    send_telegram(mesaj)
    return "ok", 200

@app.route("/")
def index():
    return "BIST ZKN Webhook Çalışıyor ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
