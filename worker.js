var TELEGRAM_TOKEN = '8411268865:AAE64-ACraM5DWtWuWoIRDxkJaI-JEzmBG0';
var SUPABASE_URL = 'https://zipyuwmxhakinuenlurx.supabase.co';
var SUPABASE_KEY = 'sb_publishable_MSaNR-WYT1nTPW1s5PxGPg_ES3OBCtz';
var ADMIN_ID = 1937674745;
var API = 'https://api.telegram.org/bot' + TELEGRAM_TOKEN;
var FREE_LIMIT = 2;
var PREMIUM_LIMIT = 50;
var UPI_ID = 'voffsilence@oksbi';

async function sendMessage(chat_id, text) {
    await fetch(API + '/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: String(chat_id), text: text, parse_mode: 'Markdown', disable_web_page_preview: true })
    });
}

function detectSite(url) {
    var u = url.toLowerCase();
    if (u.indexOf('amazon') !== -1 || u.indexOf('amzn') !== -1) return 'amazon';
    if (u.indexOf('flipkart') !== -1 || u.indexOf('fkrt') !== -1) return 'flipkart';
    return null;
}

function getAffiliateUrl(url, site) {
    if (site === 'amazon') return url.indexOf('?') !== -1 ? url + '&tag=alphabots0d-21' : url + '?tag=alphabots0d-21';
    if (site === 'flipkart') return url + '?affid=alphabots';
    return url;
}

async function getUserTrackers(chat_id) {
    var r = await fetch(SUPABASE_URL + '/rest/v1/trackers?chat_id=eq.' + chat_id + '&is_active=eq.true', {
        headers: { 'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY }
    });
    return r.json();
}

async function isPremium(chat_id) {
    var r = await fetch(SUPABASE_URL + '/rest/v1/users?chat_id=eq.' + chat_id, {
        headers: { 'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY }
    });
    var users = await r.json();
    return users.length > 0 && users[0].premium === true;
}

async function checkPrices() {
    var r = await fetch(SUPABASE_URL + '/rest/v1/trackers?is_active=eq.true', {
        headers: { 'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY }
    });
    var trackers = await r.json();
    for (var i = 0; i < trackers.length; i++) {
        var t = trackers[i];
        try {
            var resp = await fetch(t.url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }, redirect: 'follow' });
            var html = await resp.text();
            var price = null;
            if (t.site === 'amazon') {
                var m = html.match(/"price":\s*(\d+\.?\d*)/);
                if (m) price = parseFloat(m[1]);
            } else if (t.site === 'flipkart') {
                var m = html.match(/"price":\s*(\d+)/);
                if (m) price = parseFloat(m[1]);
            }
            if (price) {
                var oldPrice = t.last_price;
                await fetch(SUPABASE_URL + '/rest/v1/trackers?id=eq.' + t.id, {
                    method: 'PATCH',
                    headers: { 'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ last_price: price, last_checked: new Date().toISOString() })
                });
                if (oldPrice && price < oldPrice) {
                    var drop = oldPrice - price;
                    var pct = Math.round((drop / oldPrice) * 100);
                    await sendMessage(t.chat_id, '📉 *PRICE DROP!*\n\n💰 Old: ₹' + oldPrice + '\n🔥 New: ₹' + price + '\n📉 -' + pct + '%\n\n⚡ [Buy Now](' + getAffiliateUrl(t.url, t.site) + ')\n\n🤖 AlphaBots LTD');
                }
            }
        } catch(e) {}
    }
}

addEventListener('fetch', function(event) { event.respondWith(handleRequest(event.request)); });
addEventListener('scheduled', function(event) { event.waitUntil(checkPrices()); });

async function handleRequest(request) {
    if (request.method === 'POST') {
        try {
            var body = await request.json();
            if (body && body.message && body.message.text) {
                var msg = body.message;
                var chat_id = msg.chat.id;
                var text = msg.text;
                var name = msg.from.first_name || 'User';
                if (text.indexOf('/start') === 0) {
                    await sendMessage(chat_id, '🤖 *AlphaBots LTD*\n\n📊 Track Amazon & Flipkart prices\n🔔 Alerts every 2 hours\n\n🆓 Free: ' + FREE_LIMIT + ' links\n🔥 Premium: ' + PREMIUM_LIMIT + ' links (₹50/mo)\n\n/track <url>\n/list\n/release <id>\n/plan\n/upgrade\n/check');
                } else if (text.indexOf('/track') === 0) {
                    var parts = text.split(' ');
                    if (parts.length < 2) { await sendMessage(chat_id, '❌ /track <url>'); }
                    else {
                        var url = parts[1];
                        var site = detectSite(url);
                        if (!site) { await sendMessage(chat_id, '❌ Only Amazon & Flipkart'); }
                        else {
                            var trackers = await getUserTrackers(chat_id);
                            var premium = await isPremium(chat_id);
                            var limit = premium ? PREMIUM_LIMIT : FREE_LIMIT;
                            if (trackers.length >= limit) { await sendMessage(chat_id, '⚠️ Limit. /upgrade'); }
                            else {
                                await fetch(SUPABASE_URL + '/rest/v1/trackers', { method: 'POST', headers: { 'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' }, body: JSON.stringify({ chat_id: String(chat_id), url: url, target_price: 0, site: site, product_name: 'Product' }) });
                                await sendMessage(chat_id, '✅ *Tracking!*\n🛒 [Buy](' + getAffiliateUrl(url, site) + ')');
                            }
                        }
                    }
                } else if (text.indexOf('/list') === 0) {
                    var items = await getUserTrackers(chat_id);
                    if (!items || items.length === 0) { await sendMessage(chat_id, '📭 No trackers'); }
                    else {
                        var msg = '📊 *Trackers*\n\n';
                        for (var i = 0; i < items.length; i++) { msg += '🆔 ' + items[i].id + ' | ' + items[i].site.toUpperCase() + ' | ' + (items[i].last_price ? '₹' + items[i].last_price : 'Pending') + ' | [Buy](' + getAffiliateUrl(items[i].url, items[i].site) + ')\n'; }
                        await sendMessage(chat_id, msg);
                    }
                } else if (text.indexOf('/release') === 0) {
                    var tid = parseInt(text.split(' ')[1]);
                    if (!tid) { await sendMessage(chat_id, '❌ /release <id>'); }
                    else { await fetch(SUPABASE_URL + '/rest/v1/trackers?id=eq.' + tid + '&chat_id=eq.' + chat_id, { method: 'DELETE', headers: { 'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY } }); await sendMessage(chat_id, '✅ Released!'); }
                } else if (text.indexOf('/plan') === 0) {
                    var trackers = await getUserTrackers(chat_id);
                    var premium = await isPremium(chat_id);
                    await sendMessage(chat_id, '📊 ' + (premium ? '💎 Premium' : '🆓 Free') + ' | ' + trackers.length + '/' + (premium ? PREMIUM_LIMIT : FREE_LIMIT) + ' links');
                } else if (text.indexOf('/upgrade') === 0) {
                    await sendMessage(chat_id, '💎 *Premium* ₹50/mo\n📲 UPI: `' + UPI_ID + '`\n📩 DM @DipayanGangulyy');
                } else if (text.indexOf('/check') === 0 && chat_id === ADMIN_ID) {
                    await sendMessage(chat_id, '🔍 Checking prices...');
                    await checkPrices();
                    await sendMessage(chat_id, '✅ Done! /list');
                } else if (text.indexOf('/a_upgrade') === 0 && chat_id === ADMIN_ID) {
                    var tid = text.split(' ')[1];
                    if (tid) { await fetch(SUPABASE_URL + '/rest/v1/users', { method: 'POST', headers: { 'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json', 'Prefer': 'resolution=ignore-duplicates' }, body: JSON.stringify({ chat_id: tid, premium: true }) }); await sendMessage(chat_id, '✅ Upgraded!'); await sendMessage(tid, '🎉 *Premium!*'); }
                }
            }
        } catch(e) {}
        return new Response('OK');
    }
    return new Response('AlphaBots LTD ✅');
}
