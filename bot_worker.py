import os, requests, time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text):
    for i in range(3):
        try:
            r = requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=30)
            if r.status_code == 200: return
        except Exception as e:
            print(f"Send attempt {i+1} failed: {e}")
            time.sleep(2)

offset = 0
try:
    with open("offset.txt") as f:
        offset = int(f.read().strip())
except: pass

print(f"Offset: {offset}")

# Try multiple times to reach Telegram
resp = None
for attempt in range(3):
    try:
        r = requests.get(f"{API}/getUpdates?offset={offset}&timeout=15", timeout=30)
        resp = r.json()
        print(f"Attempt {attempt+1}: ok={resp.get('ok')}, updates={len(resp.get('result',[]))}")
        if resp.get("ok"):
            break
    except Exception as e:
        print(f"Attempt {attempt+1} error: {e}")
        time.sleep(3)

if resp and resp.get("ok"):
    for upd in resp["result"]:
        offset = upd["update_id"] + 1
        if "message" not in upd or "text" not in upd["message"]:
            continue
        msg = upd["message"]
        chat_id = msg["chat"]["id"]
        text = msg["text"]
        print(f"Processing: {text}")

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
                    send_message(chat_id, "❌ Error adding tracker")
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
                        msg += f"🆔 `{t['id']}` | {t['site'].upper()} | ₹{t['target_price']}\n"
                    send_message(chat_id, msg)
            except:
                send_message(chat_id, "❌ Error listing")
        elif text.startswith("/remove"):
            try:
                tid = int(text.split()[1])
                headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                requests.delete(f"{SUPABASE_URL}/rest/v1/trackers?id=eq.{tid}&chat_id=eq.{chat_id}", headers=headers)
                send_message(chat_id, f"✅ `{tid}` removed!")
            except:
                send_message(chat_id, "❌ Usage: `/remove <id>`")

with open("offset.txt", "w") as f:
    f.write(str(offset))
print(f"Done. Offset: {offset}")
