import os, asyncio, random, aiohttp, requests
from bs4 import BeautifulSoup
from supabase import create_client

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Use direct IP to avoid DNS issues on GitHub Actions
supabase = create_client(
    "https://lporzksrbiyznzguqean.supabase.co",
    SUPABASE_KEY,
    headers={"Host": "lporzksrbiyznzguqean.supabase.co"}
)

UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
]

def send_alert(chat_id, msg):
    try: requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

async def check_price(session, url, site):
    try:
        headers = {"User-Agent": random.choice(UA)}
        async with session.get(url, headers=headers, timeout=15) as r:
            if r.status != 200: return None
            soup = BeautifulSoup(await r.text(), "lxml")
            if site == "amazon":
                for s in [".a-price-whole", "#priceblock_dealprice"]:
                    e = soup.select_one(s)
                    if e: return float(e.get_text().replace(",","").replace("₹","").split(".")[0])
            elif site == "flipkart":
                for s in [".Nx9bqj", ".CxhGGd", "._30jeq3"]:
                    e = soup.select_one(s)
                    if e: return float(e.get_text().replace("₹","").replace(",",""))
    except: pass
    return None

async def process(item, session, sem):
    async with sem:
        price = await check_price(session, item["url"], item["site"])
        if price:
            supabase.table("trackers").update({"last_price": price, "last_checked": "now()"}).eq("id", item["id"]).execute()
            if price <= float(item["target_price"]):
                msg = f"🔥 *PRICE DROP!*\n\n🛒 {item['product_name']}\n💰 Now ₹{price} (Target: ₹{item['target_price']})\n🏷️ {item['site'].upper()}\n\n⚡ {item['url']}\n\n🤖 ALPHA BOTS"
                send_alert(item["chat_id"], msg)

async def main():
    res = supabase.table("trackers").select("*").eq("is_active", True).execute()
    if not res.data: return print("No trackers")
    print(f"Checking {len(res.data)} products...")
    sem = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as s:
        await asyncio.gather(*[process(i, s, sem) for i in res.data])
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
