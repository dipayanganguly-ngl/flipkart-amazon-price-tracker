import os, requests, sys
from supabase import create_client

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"Token: {TELEGRAM_TOKEN[:10]}...", flush=True)
print(f"Supabase URL: {SUPABASE_URL}", flush=True)

def send_message(chat_id, text):
    try:
        r = requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
        print(f"Sent to {chat_id}: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Send error: {e}", flush=True)

def detect_site(url):
    u = url.lower()
    if "amazon" in u or "amzn" in u: return "amazon"
    if "flipkart" in u or "fkrt" in u: return "flipkart"
    return None

offset = 0
try:
    with open("offset.txt") as f: offset = int(f.read().strip())
except: pass

print(f"Offset: {offset}", flush=True)

resp = requests.get(f"{API}/getUpdates?offset={offset}&timeout=5").json()
print(f"Updates: {resp.get('ok')}, Results: {len(resp.get('result', []))}", flush=True)

if resp.get("ok"):
    for upd in resp["result"]:
        offset = upd["update_id"] + 1
        if "message" not in upd or "text" not in upd["message"]: continue
        msg = upd["message"]
        chat_id = msg["chat"]["id"]
        text = msg["text"]
        print(f"Message from {chat_id}: {text}", flush=True)

        if text.startswith("/start"):
            send_message(chat_id, "🏢 *ALPHA BOTS Price Tracker*\n\n📊 Track Amazon & Flipkart prices\n🔔 Get alerts when price drops\n\n*/add <url> <price>* - Track product\n*/list* - Your trackers\n*/remove <id>* - Delete tracker")

        elif text.startswith("/add"):
            parts = text.split()
            if len(parts) < 3: send_message(chat_id, "❌ Usage: `/add <url> <target_price>`"); continue
            url = parts[1]
            try: target = float(parts[-1])
            except: send_message(chat_id, "❌ Invalid price"); continue
            site = detect_site(url)
            if not site: send_message(chat_id, "❌ Only Amazon & Flipkart URLs"); continue
            supabase.table("trackers").insert({"chat_id": str(chat_id), "url": url, "target_price": target, "site": site, "product_name": url.split("/")[-1][:30] or "Product"}).execute()
            send_message(chat_id, f"✅ *Tracker Added!*\n\n🛒 {site.upper()}\n💰 Target: ₹{target}")

        elif text.startswith("/list"):
            res = supabase.table("trackers").select("*").eq("chat_id", str(chat_id)).eq("is_active", True).execute()
            if not res.data: send_message(chat_id, "📭 No trackers. Use /add")
            else:
                msg = "📊 *Your Trackers*\n\n"
                for t in res.data: msg += f"🆔 `{t['id']}` | {t['site'].upper()} | ₹{t['target_price']}\n"
                send_message(chat_id, msg)

        elif text.startswith("/remove"):
            try:
                tid = int(text.split()[1])
                supabase.table("trackers").update({"is_active": False}).eq("id", tid).eq("chat_id", str(chat_id)).execute()
                send_message(chat_id, f"✅ Tracker `{tid}` removed!")
            except: send_message(chat_id, "❌ Usage: `/remove <id>`")

with open("offset.txt", "w") as f: f.write(str(offset))
print(f"Done. New offset: {offset}", flush=True)
