import time
import hashlib
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL = "https://adhahi.dz/register"
TARGET = "أم البواقي"
STATE_FILE = "state.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        log(f"خطأ في الإرسال: {e}")

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_status": None, "last_hash": None}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(status, hash_val):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_status": status, "last_hash": hash_val}, f)

def fetch_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=30000)
        page.wait_for_timeout(5000)
        content = page.content()
        browser.close()
        return content

def analyze(content):
    if TARGET not in content:
        return "NOT_FOUND"
    lines = content.split('\n')
    for line in lines:
        if TARGET in line:
            if "غير متوفر" in line:
                return "CLOSED"
            elif "متوفر" in line:
                return "OPEN"
    return "UNKNOWN"

def get_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

log("البوت بدأ يعمل...")
send("🟢 بوت أضحية أم البواقي بدأ يعمل!\nسيراقب الموقع كل 30 ثانية.")

while True:
    try:
        log("جاري فحص الموقع...")
        html = fetch_page()
        current_hash = get_hash(html)
        status = analyze(html)
        state = load_state()
        log(f"الحالة: {status}")

        if current_hash != state["last_hash"]:
            log("تغيير في الصفحة!")
            if status == "OPEN" and state["last_status"] != "OPEN":
                send(
                    "🚨🚨🚨 تنبيه عاجل!\n\n"
                    "✅ فُتح الحجز في ولاية أم البواقي!\n\n"
                    "👉 اذهب للموقع الآن:\nhttps://adhahi.dz/register\n\n"
                    "⏰ سارع قبل نفاد الأماكن!"
                )
            elif status == "NOT_FOUND":
                send("⚠️ تغيّر شكل الموقع - تحقق يدوياً")
            save_state(status, current_hash)
        else:
            log("لا تغيير")

    except Exception as e:
        log(f"خطأ: {e}")

    time.sleep(30)
