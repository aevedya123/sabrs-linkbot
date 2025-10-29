import os
import time
import re
import requests
import discord
from discord.ext import tasks, commands
from keep_alive import keep_alive

# Start the Flask server
keep_alive()

# --- Environment Variables ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

# --- Discord Bot Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Roblox API ---
ROBLOX_API_URL = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
HEADERS = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}", "User-Agent": "Mozilla/5.0"}
FETCH_LIMIT = 25  # must be one of 10, 25, 50, 100

# --- Storage for seen post IDs ---
seen_posts = set()

# --- Extract Links Function ---
def extract_links(text):
    url_pattern = r'(https?://[^\s]+)'
    return re.findall(url_pattern, text)

def fetch_group_posts():
    try:
        response = requests.get(ROBLOX_API_URL, headers=HEADERS, params={"sortOrder": "Desc", "limit": FETCH_LIMIT})
        if response.status_code != 200:
            print(f"Roblox response status: {response.status_code}")
            print("Error:", response.text)
            return []
        return response.json().get("data", [])
    except Exception as e:
        print("Error fetching wall:", e)
        return []

@bot.event
async def on_ready():
    print("✅ Bot started successfully and is now monitoring Roblox wall posts for links...")
    monitor_wall.start()

@tasks.loop(minutes=1)
async def monitor_wall():
    global seen_posts
    posts = fetch_group_posts()
    if not posts:
        print("⚠️ No posts found or API error.")
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
            links_to_send = new_links[:20]  # limit to 20 per minute
            embed = discord.Embed(
                title="🔗 New Links Found on Roblox Group Wall",
                description="\n".join(links_to_send),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Fetched from Group ID: {GROUP_ID}")
            await channel.send(embed=embed)
            print(f"✅ Sent {len(links_to_send)} links to Discord.")
        else:
            print("⚠️ Discord channel not found.")
    else:
        print("ℹ️ No new links detected.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
