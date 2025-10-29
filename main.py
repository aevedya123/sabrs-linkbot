import os
import discord
import aiohttp
import asyncio
import re
from discord.ext import tasks

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# To avoid duplicate link posts
seen_links = set()

def extract_links(text):
    pattern = r"https?://[^\s]+"
    return re.findall(pattern, text)

async def fetch_group_wall():
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "User-Agent": "Roblox/WinInet",
        "Content-Type": "application/json"
    }

    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"⚠️ Failed to fetch group wall: {response.status}")
                return []

            data = await response.json()
            posts = data.get("data", [])
            links = []
            for post in posts:
                content = post.get("body", "")
                found = extract_links(content)
                for link in found:
                    if link not in seen_links:
                        seen_links.add(link)
                        links.append(link)
            return links

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    check_wall.start()

@tasks.loop(minutes=1)
async def check_wall():
    print("🔍 Checking Roblox group wall...")
    new_links = await fetch_group_wall()

    if not new_links:
        print("❌ No new links found.")
        return

    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel not found.")
        return

    message = "\n".join(new_links)
    await channel.send(f"**✅️ New Roblox Scammer Links Found:**\n{message}")
    print(f"✅ Posted {len(new_links)} new links to Discord.")

client.run(DISCORD_TOKEN)
