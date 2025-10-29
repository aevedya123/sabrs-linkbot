import os
import discord
from discord.ext import tasks, commands
import requests
import asyncio
from keep_alive import keep_alive
keep_alive()

# Load environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# To track already sent links
sent_links = set()

def fetch_links():
    """Fetch the latest posts from Roblox group wall and extract links."""
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        posts = data.get("data", [])
        links = []

        for post in posts:
            content = post.get("body", "")
            # Extract all links
            words = content.split()
            for word in words:
                if word.startswith("http://") or word.startswith("https://"):
                    links.append(word)

        # Remove duplicates
        unique_links = list(dict.fromkeys(links))
        return unique_links[:20]  # Limit to around 20 per fetch

    except Exception as e:
        print(f"⚠️ Error fetching links: {e}")
        return []

@tasks.loop(minutes=1)
async def fetch_and_send_links():
    """Fetch new links every minute and send to Discord."""
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Channel not found. Check CHANNEL_ID.")
            return

        links = fetch_links()
        new_links = [link for link in links if link not in sent_links]

        if new_links:
            sent_links.update(new_links)
            embed = discord.Embed(
                title="🕹️ New Roblox Group Links",
                description="\n".join(new_links),
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            print(f"✅ Sent {len(new_links)} new links.")
        else:
            print("ℹ️ No new links found.")

    except Exception as e:
        print(f"⚠️ Error sending links: {e}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    fetch_and_send_links.start()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
