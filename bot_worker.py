import os, requests, time, socket

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Force IPv4
import urllib3
urllib3.util.connection.HAS_IPV6 = False

API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text):
    try:
        r = requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=30)
        print(f"Send status: {r.status_code}")
    except Exception as e:
        print(f"Send error: {e}")

offset = 0
try:
    with open("offset.txt") as f:
        offset = int(f.read().strip())
except: pass

print(f"Offset: {offset}")

# Direct request to Telegram
try:
    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter())
    r = session.get(f"{API}/getUpdates?offset={offset}&timeout=10", timeout=30)
    print(f"Status: {r.status_code}")
    resp = r.json()
    print(f"OK: {resp.get('ok')}, Updates: {len(resp.get('result',[]))}")
except Exception as e:
    print(f"Error: {e}")
    resp = None

if resp and resp.get("ok"):
    for upd in resp["result"]:
        offset = upd["update_id"] + 1
        if "message" not in upd or "text" not in upd["message"]:
            continue
        msg = upd["message"]
        chat_id = msg["chat"]["id"]
        text = msg["text"]

        if text.startswith("/start"):
            send_message(chat_id, "🏢 *ALPHA BOTS Price Tracker*\n\n📊 Track Amazon & Flipkart prices\n\n*/add <url> <price>* - Track\n*/list* - Trackers\n*/remove <id>* - Delete")
        elif text.startswith("/add"):
            parts = text.split()
            if len(parts) < 3:
                send_message(chat_id, "❌ Usage: `/add <url> <price>`")
            else:
                try:
                    url = parts[1]
                    target = float(parts[-1])
                    site = "amazon" if "amazon" in url.lower() else "flipkart"
                    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
                    requests.post(f"{SUPABASE_URL}/rest/v1/trackers", headers=headers, json={"chat_id": str(chat_id), "url": url, "target_price": target, "site": site, "product_name": "Product"})
                    send_message(chat_id, f"✅ *Tracker Added!*\n💰 Target: ₹{target}")
                except:
                    send_message(chat_id, "❌ Error")
        elif text.startswith("/list"):
            try:
                headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                r = requests.get(f"{SUPABASE_URL}/rest/v1/trackers?chat_id=eq.{chat_id}&is_active=eq.true", headers=headers)
                items = r.json()
                if not items:
                    send_message(chat_id, "📭 No trackers")
                else:
                    msg = "📊 *Trackers*\n\n"
                    for t in items:
                        msg += f"🆔 {t['id']} | {t['site'].upper()} | ₹{t['target_price']}\n"
                    send_message(chat_id, msg)
            except:
                pass
        elif text.startswith("/remove"):
            try:
                tid = int(text.split()[1])
                headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                requests.delete(f"{SUPABASE_URL}/rest/v1/trackers?id=eq.{tid}&chat_id=eq.{chat_id}", headers=headers)
                send_message(chat_id, f"✅ Removed")
            except:
                pass

with open("offset.txt", "w") as f:
    f.write(str(offset))
