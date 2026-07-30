import os, requests, re
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

r = requests.get(f"{SUPABASE_URL}/rest/v1/trackers?is_active=eq.true", headers=headers)
trackers = r.json()
print(f"Checking {len(trackers)} products...")

for t in trackers:
    try:
        resp = requests.get(t['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, allow_redirects=True)
        html = resp.text
        price = None
        
        if t['site'] == 'amazon':
            m = re.search(r'"price":\s*(\d+\.?\d*)', html)
            if m: price = float(m.group(1))
        elif t['site'] == 'flipkart':
            m = re.search(r'"price":\s*(\d+)', html)
            if m: price = float(m.group(1))
        
        if price:
            old = t.get('last_price')
            requests.patch(f"{SUPABASE_URL}/rest/v1/trackers?id=eq.{t['id']}", headers=headers, 
                json={"last_price": price, "last_checked": datetime.now().isoformat()})
            print(f"✅ {t['site']}: ₹{price}" + (f" (was ₹{old})" if old else ""))
    except Exception as e:
        print(f"❌ {t['url'][:50]}: {e}")

print("Done! Cloudflare Worker will send alerts on drops.")
