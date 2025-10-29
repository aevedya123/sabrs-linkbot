import os
import discord
import asyncio
import aiohttp
from keep_alive import keep_alive
from discord.ext import tasks, commands

# ====== CONFIG ======
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL"))
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")  # e.g., "1234567"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Keep track of posted links to avoid duplicates
posted_links = set()

# Roblox group wall API
GROUP_WALL_URL = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"

# ====== FETCH LINKS ======
async def fetch_links():
    async with aiohttp.ClientSession() as session:
        async with session.get(GROUP_WALL_URL) as response:
            if response.status != 200:
                print("Failed to fetch group wall.")
                return []
            data = await response.json()

    posts = data.get("data", [])
    links = []
    for post in posts:
        content = post.get("body", "")
        # Extract potential links
        found_links = []
        for word in content.split():
            if word.startswith("http://") or word.startswith("https://"):
                found_links.append(word)
        links.extend(found_links)
    return links

# ====== POST TO DISCORD ======
async def post_new_links():
    links = await fetch_links()
    new_links = [l for l in links if l not in posted_links]

    if not new_links:
        print("No new links found.")
        return

    # Add new links to posted set
    posted_links.update(new_links)

    # Limit to 20 links per batch
    batch = new_links[:20]

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🕹️ New Roblox Group Links",
            description="\n".join(batch),
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)
        print(f"Posted {len(batch)} new links.")
    else:
        print("Channel not found!")

# ====== LOOP EVERY MINUTE ======
@tasks.loop(minutes=1)
async def fetch_loop():
    await post_new_links()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    fetch_loop.start()
keep_alive()
bot.run(TOKEN)
