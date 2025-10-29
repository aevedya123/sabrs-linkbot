import os
import time
import requests
import discord
from discord.ext import tasks, commands
from keep_alive import keep_alive

# Start web server for uptime pings
keep_alive()

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

# Roblox API settings
ROBLOX_API_URL = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
FETCH_LIMIT = 25  # Allowed values: 10, 25, 50, 100

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Track seen posts
seen_posts = set()

def fetch_group_wall():
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "sortOrder": "Desc",
        "limit": FETCH_LIMIT
    }
    try:
        response = requests.get(ROBLOX_API_URL, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Roblox response status: {response.status_code}")
            print("Error:", response.text)
            return []
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print("Error fetching wall:", e)
        return []

@bot.event
async def on_ready():
    print("✅ Bot started successfully and is now monitoring the group wall!")
    monitor_wall.start()

@tasks.loop(minutes=1)
async def monitor_wall():
    global seen_posts
    posts = fetch_group_wall()
    if not posts:
        print("No posts found or API error.")
        return

    new_links = []
    for post in posts:
        post_id = post["id"]
        if post_id not in seen_posts:
            seen_posts.add(post_id)
            new_links.append(f"https://www.roblox.com/groups/{GROUP_ID}/wall#!/post/{post_id}")

    if new_links:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            links_to_send = new_links[:20]  # Limit to 20 per minute
            await channel.send("\n".join(links_to_send))
            print(f"✅ Sent {len(links_to_send)} new links to Discord.")
        else:
            print("⚠️ Channel not found.")
    else:
        print("ℹ️ No new posts detected.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
