import os
import requests
import re
import asyncio
import discord
from discord.ext import tasks
from datetime import datetime, timezone

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
GROUP_ID = os.getenv("GROUP_ID")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def get_group_wall_posts():
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?sortOrder=Desc&limit=100"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error {response.status_code} fetching posts.")
        return []

    data = response.json().get("data", [])
    posts_with_links = []

    for post in data:
        body = post.get("body", "")
        # Capture links even if inside markdown/hyperlinks
        links = re.findall(r"(https?://[^\s]+|roblox\.com/[^\s)]+)", body)
        if links:
            timestamp = datetime.fromisoformat(post["created"].replace("Z", "+00:00"))
            posts_with_links.append({
                "author": post.get("poster", {}).get("username", "Unknown"),
                "time": timestamp,
                "links": links
            })
    return posts_with_links

@tasks.loop(minutes=1)
async def fetch_and_send_links():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Channel not found.")
        return

    print("🔍 Fetching latest Roblox posts...")
    posts = get_group_wall_posts()
    if not posts:
        await channel.send("⚠️ No links found in recent posts.")
        return

    # Sort posts by time, get newest 20
    posts = sorted(posts, key=lambda x: x["time"], reverse=True)[:20]

    embed = discord.Embed(
        title="🕹️ Latest Roblox Group Links",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    for post in posts:
        joined_links = "\n".join(post["links"])
        embed.add_field(
            name=f"{post['author']} • {post['time'].strftime('%H:%M:%S UTC')}",
            value=joined_links,
            inline=False
        )

    await channel.send(embed=embed)
    print("✅ Sent 20 latest links to Discord.")

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    fetch_and_send_links.start()

client.run(DISCORD_TOKEN)
