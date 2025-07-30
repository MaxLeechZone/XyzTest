from pyrogram import Client, filters, idle
from pyrogram.types import Message
import re, asyncio, time
from collections import defaultdict

# 🛠️ Set these values via environment variables in Replit
API_ID = int(__import__('os').env['API_ID'])
API_HASH = __import__('os').env['API_HASH']
BOT_TOKEN = __import__('os').env['BOT_TOKEN']
SOURCE_CHANNEL = __import__('os').env['SOURCE_CHANNEL']
DEST_CHANNEL = __import__('os').env['DEST_CHANNEL']
OWNER_ID = int(__import__('os').env['OWNER_ID'])

movie_cache = defaultdict(set)
active_tasks = {}
start_time = time.time()

bot = Client("quality_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def on_startup():
    try:
        dest_chat = await bot.get_chat(DEST_CHANNEL)
        await bot.send_message(chat_id=DEST_CHANNEL,
                               text=f"🤖 Bot Restarted & Ready!\n✅ Connected to <b>{dest_chat.title}</b>")
        print("✅ Startup OK — Connected to", dest_chat.title)
    except Exception as e:
        print("❌ Startup Error:", e)

def clean_title(raw_title):
    remove = ["HDRip","BluRay","WEBRip","WEB-DL","ESubs","SkymoviesHD","x264","x265",
              "Dual Audio","Hindi","English","DDP","DD","HEVC","Credit","UnRated","AAC","5.1","2.0"]
    parts = raw_title.replace('.', ' ').split()
    return ' '.join([p for p in parts if p not in remove and not re.match(r'\d{3,4}p', p)]).strip()

def extract_title_quality(text: str):
    import re
    match = re.search(r"([A-Za-z0-9\.\s]+)[\.\s](19|20)\d{2}[\.\s](\d{3,4}p)", text)
    if match:
        clean_name = clean_title(match.group(1).strip())
        return f"{clean_name} ({match.group(2)})", match.group(3)
    m = re.search(r"([A-Za-z0-9\s]+)\s+\((19|20)\d{2}\)", text)
    q = re.search(r"(\d{3,4}p)", text)
    if m and q:
        return f"{m.group(1).strip()} ({m.group(2)})", q.group(1)
    return None, None

async def send_final_message(title):
    await asyncio.sleep(3)
    quals = sorted(movie_cache[title], key=lambda x: int(x.replace('p','')))
    await bot.send_message(chat_id=DEST_CHANNEL,
                           text=f"<b>{title}</b>\nAvailable Qualities: <code>{' / '.join(quals)}</code>\n\n✅ Added On Website")
    movie_cache.pop(title, None)
    active_tasks.pop(title, None)

@bot.on_message(filters.channel & filters.chat(SOURCE_CHANNEL))
async def handler(_, message: Message):
    content = message.text or message.caption or ""
    title, quality = extract_title_quality(content)
    if title and quality:
        movie_cache[title].add(quality)
        if title in active_tasks:
            active_tasks[title].cancel()
        active_tasks[title] = asyncio.create_task(send_final_message(title))

@bot.on_message(filters.command("start") & filters.private)
async def cmd_start(_, message: Message):
    await message.reply("I'm online and active ✅")

@bot.on_message(filters.command("admin") & filters.user(OWNER_ID))
async def cmd_admin(_, message: Message):
    up = int(time.time() - start_time)
    h, rem = divmod(up, 3600); m, s = divmod(rem, 60)
    await message.reply(f"Uptime: {h}h {m}m {s}s")

async def main():
    await bot.start()
    await on_startup()
    await idle()
    await bot.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
