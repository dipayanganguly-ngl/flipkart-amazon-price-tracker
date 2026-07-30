import os, requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

# Get offset
offset = 0
try:
    with open("offset.txt") as f:
        offset = int(f.read().strip())
except:
    pass

print(f"Offset: {offset}")

# Get updates
try:
    resp = requests.get(f"{API}/getUpdates?offset={offset}&timeout=10").json()
    print(f"API response ok: {resp.get('ok')}")
    print(f"Updates: {len(resp.get('result', []))}")
except Exception as e:
    print(f"API error: {e}")
    resp = {"ok": False, "result": []}

if resp.get("ok"):
    for upd in resp["result"]:
        offset = upd["update_id"] + 1
        
        if "message" not in upd or "text" not in upd["message"]:
            continue
        
        msg = upd["message"]
        chat_id = msg["chat"]["id"]
        text = msg["text"]
        
        print(f"Message from {chat_id}: {text}")

        if text.startswith("/start"):
            send_message(chat_id, "🏢 *ALPHA BOTS Price Tracker*\n\n📊 Track Amazon & Flipkart prices\n🔔 Alerts when price drops\n\n*/add <url> <price>* - Track\n*/list* - Your trackers\n*/remove <id>* - Delete")
            print("Sent /start reply")

        elif text.startswith("/add"):
            parts = text.split()
            if len(parts) < 3:
                send_message(chat_id, "❌ Usage: `/add <url> <target_price>`")
            else:
                url = parts[1]
                try:
                    target = float(parts[-1])
                    # Save to Supabase
                    import json
                    headers = {
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    }
                    data = {
                        "chat_id": str(chat_id),
                        "url": url,
                        "target_price": target,
                        "site": "amazon" if "amazon" in url.lower() else "flipkart",
                        "product_name": "Product"
                    }
                    r = requests.post(f"{SUPABASE_URL}/rest/v1/trackers", headers=headers, json=data)
                    print(f"Supabase insert: {r.status_code}")
                    send_message(chat_id, f"✅ *Tracker Added!*\n💰 Target: ₹{target}")
                except Exception as e:
                    print(f"Add error: {e}")
                    send_message(chat_id, f"❌ Error: {str(e)[:50]}")

        elif text.startswith("/list"):
            try:
                headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                r = requests.get(f"{SUPABASE_URL}/rest/v1/trackers?chat_id=eq.{chat_id}&is_active=eq.true", headers=headers)
                items = r.json()
                if not items:
                    send_message(chat_id, "📭 No trackers. Use /add")
                else:
                    msg = "📊 *Your Trackers*\n\n"
                    for t in items:
                        msg += f"🆔 `{t['id']}` | {t['site'].upper()} | ₹{t['target_price']}\n"
                    send_message(chat_id, msg)
                print(f"List: {len(items)} items")
            except Exception as e:
                print(f"List error: {e}")

        elif text.startswith("/remove"):
            try:
                tid = int(text.split()[1])
                headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                r = requests.delete(f"{SUPABASE_URL}/rest/v1/trackers?id=eq.{tid}&chat_id=eq.{chat_id}", headers=headers)
                send_message(chat_id, f"✅ Tracker `{tid}` removed!")
            except:
                send_message(chat_id, "❌ Usage: `/remove <id>`")

# Save offset
with open("offset.txt", "w") as f:
    f.write(str(offset))

print(f"Saved offset: {offset}")
