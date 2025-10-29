import os
import time
import requests
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from keep_alive import keep_alive
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    post_links.start()

@tasks.loop(minutes=1)
async def post_links():
    """Fetches ~20 latest group wall posts and sends unique ones to Discord."""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel not found. Check CHANNEL_ID.")
        return

    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "User-Agent": "RobloxWallFetcher/1.0",
        "Accept": "application/json"
    }

    url = f"https://groups.roblox.com/v1/groups/{GROUP_ID}/wall/posts?limit=20&sortOrder=Desc"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Ensure valid response
        if "data" not in data:
            print("⚠️ Invalid data received.")
            return

        posts = data["data"]
        print(f"Fetched {len(posts)} posts.")

        # Keep track of posted IDs
        if not hasattr(post_links, "posted_ids"):
            post_links.posted_ids = set()

        for post in posts:
            post_id = post.get("id")
            if post_id and post_id not in post_links.posted_ids:
                content = post.get("body", "").strip()
                if content:
                    msg = f"💬 **New Wall Post:** {content[:1900]}"  # truncate if too long
                    await channel.send(msg)
                post_links.posted_ids.add(post_id)

    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

bot.run(DISCORD_TOKEN)                            try:
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
keep_alive()
