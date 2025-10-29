import os
import re
import json
import asyncio
from datetime import datetime
from threading import Thread
import aiohttp
import discord
from discord import Embed
from flask import Flask

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) if os.getenv("CHANNEL_ID") else None
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

if not DISCORD_TOKEN:
    raise SystemExit("Missing DISCORD_TOKEN env var.")
if not CHANNEL_ID:
    raise SystemExit("Missing CHANNEL_ID env var.")
if not GROUP_ID:
    raise SystemExit("Missing GROUP_ID env var.")
if not ROBLOX_COOKIE:
    raise SystemExit("Missing ROBLOX_COOKIE env var.")

CHECK_INTERVAL = 60
POSTED_FILE = "posted_links.json"
USER_AGENT = "SABRS-LinkBot/1.0"
SHARE_REGEX = re.compile(r"https?://(?:www\.)?roblox\.com/share\?[^\s)\"'<>]+", re.IGNORECASE)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def load_posted():
    if not os.path.exists(POSTED_FILE):
        return set()
    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except:
        return set()

def save_posted(posted_set):
    try:
        with open(POSTED_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(posted_set)), f, indent=2)
    except:
        pass

async def fetch_group_wall(session, limit=20):
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?limit={limit}&sortOrder=Desc"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"
    }
    try:
        async with session.get(url, headers=headers, timeout=25) as resp:
            if resp.status == 200:
                j = await resp.json()
                return j.get("data", [])
            elif resp.status == 429:
                raise RuntimeError("ROBLOX_RATE_LIMIT")
            else:
                return []
    except:
        return []

def extract_share_links_from_text(text):
    if not text:
        return []
    return SHARE_REGEX.findall(text)

async def poll_loop():
    await client.wait_until_ready()
    posted = load_posted()
    backoff_seconds = 0
    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                if backoff_seconds > 0:
                    await asyncio.sleep(backoff_seconds)
                posts = await fetch_group_wall(session, limit=20) 
                
                new_items = []
                for post in reversed(posts):
                    body = post.get("body", "") or ""
                    post_id = str(post.get("id") or post.get("postId") or "")
                    links = extract_share_links_from_text(body)
                    for link in links:
                        key = f"{post_id}|{link}"
                        if key not in posted:
                            new_items.append((link, key))
                if new_items:
                    try:
                        channel = await client.fetch_channel(CHANNEL_ID)
                    except:
                        channel = None
                    if channel:
                        BATCH = 10
                        all_links = [li for li, _ in new_items]
                        for i in range(0, len(all_links), BATCH):
                            chunk = all_links[i:i+BATCH]
                            description = "\n".join(f"• {c}" for c in chunk)
                            embed = Embed(title="🔗 New Roblox Share Links", description=description, color=0x00FFCC, timestamp=datetime.utcnow())
                            embed.set_footer(text="Made By SAB-RS")
                            try:
                                await channel.send(embed=embed)
                            except:
                                continue
                        for _, key in new_items:
                            posted.add(key)
                        save_posted(posted)
                backoff_seconds = 0
                await asyncio.sleep(CHECK_INTERVAL)
            except RuntimeError as rte:
                if str(rte) == "ROBLOX_RATE_LIMIT":
                    backoff_seconds = max(60, (backoff_seconds or 60) * 2)
                    backoff_seconds = min(backoff_seconds, 3600)
                    await asyncio.sleep(backoff_seconds)
                else:
                    await asyncio.sleep(60)
            except:
                await asyncio.sleep(60)

app = Flask("keepalive")

@app.route("/")
def home():
    return "SABRS-LinkBot - running"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

@client.event
async def on_ready():
    if not getattr(client, "_polling_started", False):
        client._polling_started = True
        client.loop.create_task(poll_loop())

if __name__ == "__main__":
    t = Thread(target=run_flask, daemon=True)
    t.start()
    client.run(DISCORD_TOKEN)
