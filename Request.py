from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import re
import asyncio
from collections import defaultdict
from urllib.parse import quote_plus

API_ID = 23897874
API_HASH = "ec91dd01da9693911a6ee4af5d0bef2c"
BOT_TOKEN = "8009487835:AAHEma1rrf3VLlJPnXnC0rUKMYL-n181Jfo"

SOURCE_CHANNEL = -1002540685561
DEST_CHANNEL = -1002857534336

bot = Client("quality_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

movie_cache = defaultdict(set)
active_tasks = {}

def clean_title(raw_title):
    remove_keywords = [
        "HDRip", "BluRay", "WEBRip", "WEB-DL", "ESubs", "SkymoviesHD", "x264", "x265",
        "Dual Audio", "Hindi", "English", "DDP", "DD", "HEVC", "Credit", "UnRated", "AAC", "5.1", "2.0"
    ]
    parts = raw_title.replace('.', ' ').split()
    clean_parts = [p for p in parts if p.lower() not in map(str.lower, remove_keywords) and not re.match(r'\d{3,4}p', p)]
    return ' '.join(clean_parts).strip()

def extract_title_quality(text: str):
    match = re.search(r"([A-Za-z0-9\.\s]+)[\.\s](19|20)\d{2}[\.\s](\d{3,4}p)", text)
    if not match:
        match2 = re.search(r"([A-Za-z0-9\s]+)\s+\((19|20)\d{2}\)", text)
        quality = re.search(r"(\d{3,4}p)", text)
        if match2 and quality:
            title = match2.group(1).strip()
            year = match2.group(2) + text[match2.end(2):match2.end(2)+2]
            return f"{title} ({year})", quality.group(1)
        return None, None

    raw_title = match.group(1).strip()
    clean_name = clean_title(raw_title)
    year_match = re.search(r"(19|20)\d{2}", text)
    year = year_match.group(0) if year_match else "Unknown"
    quality = match.group(3)
    return f"{clean_name} ({year})", quality

async def send_final_message(title):
    await asyncio.sleep(3)
    qualities = sorted(movie_cache[title], key=lambda x: int(x.replace('p', '')))
    msg = f"{title}\nAvailable Qualities: {' / '.join(qualities)}\n\nAdded On Site ✅️"

    search_query = quote_plus(title)
    website_url = f"https://maxmediaserver.vercel.app/search/{search_query}"

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Watch Here", url=website_url)]]
    )

    try:
        await bot.send_message(chat_id=DEST_CHANNEL, text=msg, reply_markup=keyboard)
    except Exception as e:
        print(f"Failed to send message: {e}")

    del movie_cache[title]
    del active_tasks[title]

@bot.on_message(filters.channel & filters.chat(SOURCE_CHANNEL))
async def process_message(_, message: Message):
    content = (message.text or message.caption or "").replace('\n', ' ')
    if not content:
        return

    title, quality = extract_title_quality(content)
    if not title or not quality:
        return

    movie_cache[title].add(quality)

    if title in active_tasks:
        active_tasks[title].cancel()

    active_tasks[title] = asyncio.create_task(send_final_message(title))

bot.run()
