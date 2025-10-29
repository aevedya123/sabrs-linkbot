import os
import time
import re
import requests
import discord
from discord.ext import tasks, commands
from keep_alive import keep_alive

keep_alive()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}", "User-Agent": "Mozilla/5.0"}
ROBLOX_API_URL = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
FETCH_LIMIT = 25  # allowed: 10, 25, 50, 100

seen_posts = set()

def extract_links(text):
    pattern = r"(https?://[^\s]+)"
    return re.findall(pattern, text)

def fetch_posts():
    try:
        r = requests.get(ROBLOX_API_URL, headers=HEADERS, params={"sortOrder": "Desc", "limit": FETCH_LIMIT})
        if r.status_code != 200:
            print("Roblox response:", r.status_code, r.text)
            return []
        return r.json().get("data", [])
    except Exception as e:
        print("Error fetching posts:", e)
        return []

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is live and monitoring the group wall!")
    monitor_wall.start()

@tasks.loop(minutes=1)
async def monitor_wall():
    global seen_posts
    posts = fetch_posts()
    if not posts:
        print("⚠️ No posts found or error.")
        return

    new_links = []
    for post in posts:
        post_id = post["id"]
        if post_id not in seen_posts:
            seen_posts.add(post_id)
            links = extract_links(post["body"])
            if links:
                new_links.extend(links)

    if new_links:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🔗 New Links Found on Roblox Group Wall",
                description="\n".join(new_links[:20]),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Fetched from Group ID: {GROUP_ID}")
            await channel.send(embed=embed)
            print(f"✅ Sent {len(new_links[:20])} links to Discord.")
    else:
        print("ℹ️ No new links detected this cycle.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
