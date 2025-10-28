# bot.py
import os, re, json, asyncio, aiohttp, discord
from discord import Embed

# --- CONFIG ---
GROUP_ID = "35815907"   # Roblox group ID
POLL_SECONDS = 60        # How often to check (in seconds)
POSTED_FILE = "posted_links.json"
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# --- DISCORD CLIENT ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# --- HELPERS ---
def load_posted():
    """Load already sent links from file"""
    if not os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "w") as f:
            json.dump([], f)
        return set()
    try:
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted), f)

async def fetch_posts(session):
    """Fetch posts from Roblox group wall"""
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?limit=100"
    async with session.get(url) as r:
        if r.status != 200:
            raise RuntimeError(f"Roblox API error {r.status}")
        data = await r.json()
        return data.get("data", [])

def extract_links(text):
    """Find only roblox.com/share links"""
    if not text:
        return []
    return re.findall(r"https?://(?:www\.)?roblox\.com/share[^\s)]+", text)

async def process(session, posted):
    """Process new posts and send embeds if new links found"""
    posts = await fetch_posts(session)
    new_links = []
    for post in reversed(posts):
        links = extract_links(post.get("body", ""))
        for link in links:
            key = f"{post.get('id')}|{link}"
            if key not in posted:
                new_links.append(link)
                posted.add(key)

    if not new_links:
        return 0

    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel not found.")
        return 0

    # Send in chunks of 10 per embed
    for i in range(0, len(new_links), 10):
        chunk = new_links[i:i+10]
        embed = Embed(
            title="🔗 New Roblox Share Links Found",
            description="\n".join(f"• {l}" for l in chunk),
            color=0x00FFCC
        )
        embed.set_footer(text="Made By SAB-RS")
        await channel.send(embed=embed)

    save_posted(posted)
    return len(new_links)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    posted = load_posted()
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                new = await process(session, posted)
                print(f"Checked — {new} new links.")
            except Exception as e:
                print("Error:", e)
            await asyncio.sleep(POLL_SECONDS)

if __name__ == "__main__":
    client.run(TOKEN)
