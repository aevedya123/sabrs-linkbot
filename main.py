import os
import discord
import requests
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
COOKIE = os.getenv("ROBLOX_COOKIE")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

sent = set()

async def get_links():
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
    headers = {
        "Cookie": f".ROBLOSECURITY={COOKIE}",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        posts = data.get("data", [])
        links = []
        for post in posts:
            for word in post.get("body", "").split():
                if word.startswith("http://") or word.startswith("https://"):
                    links.append(word)
        return list(dict.fromkeys(links))[:20]
    except Exception as e:
        print("Error:", e)
        return []

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    while True:
        try:
            links = await asyncio.to_thread(get_links)
            new = [l for l in links if l not in sent]
            if new:
                sent.update(new)
                await channel.send("\n".join(new))
                print(f"Sent {len(new)} new links.")
            else:
                print("No new links.")
        except Exception as e:
            print("Loop error:", e)
        await asyncio.sleep(60)  # every 1 minute

client.run(TOKEN)
