import os
import discord
import requests
import asyncio
from keep_alive import keep_alive
keep_alive()
# Environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
COOKIE = os.getenv("ROBLOX_COOKIE")

# Discord client setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)

sent_links = set()

def get_links():
    """Fetch up to 20 links from the Roblox group wall."""
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
    headers = {
        "Cookie": f".ROBLOSECURITY={COOKIE}",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        posts = data.get("data", [])
        links = []
        for post in posts:
            body = post.get("body", "")
            for word in body.split():
                if word.startswith("http://") or word.startswith("https://"):
                    links.append(word)
        return list(dict.fromkeys(links))[:20]
    except Exception as e:
        print("Error fetching links:", e)
        return []

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found! Check CHANNEL_ID or bot permissions.")
        return

    # Confirmation message
    try:
        await channel.send("✅ Bot started successfully and is now monitoring the group wall!")
    except Exception as e:
        print("Error sending startup message:", e)

    # Main loop
    while True:
        links = get_links()
        if links:
            new_links = [l for l in links if l not in sent_links]
            if new_links:
                sent_links.update(new_links)
                msg = "\n".join(new_links)
                try:
                    await channel.send(msg)
                    print(f"📤 Sent {len(new_links)} new links.")
                except Exception as e:
                    print("Error sending links:", e)
            else:
                print("ℹ️ No new links found.")
        else:
            print("⚠️ No links found on group wall.")
        await asyncio.sleep(60)  # Check every minute

client.run(TOKEN)
