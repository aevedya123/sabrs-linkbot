import os
import time
import discord
import requests
import asyncio
import re
from keep_alive import keep_alive
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

if not TOKEN or not CHANNEL_ID or not GROUP_ID or not ROBLOX_COOKIE:
    raise SystemExit("Missing one of required env vars: DISCORD_TOKEN, CHANNEL_ID, GROUP_ID, ROBLOX_COOKIE")

CHANNEL_ID = int(CHANNEL_ID)
GROUP_ID = str(GROUP_ID)

client = discord.Client(intents=discord.Intents.default())

SHARE_RE = re.compile(r"https?://[^\s]*roblox\.com/share[^\s]*|roblox\.com/share[^\s]*", re.IGNORECASE)
FETCH_LIMIT = 20
SLEEP_SECONDS = 60
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SABRS-LinkBot/1.0)",
    "Accept": "application/json",
    "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"
}

sent = set()

def fetch_group_posts():
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?limit={FETCH_LIMIT}&sortOrder=Desc"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        print("HTTP request failed:", e)
        return None, f"request-exception: {e}"
    print("Roblox response status:", r.status_code)
    if r.status_code != 200:
        text = r.text[:1000].replace("\n", " ")
        return None, f"bad-status-{r.status_code}: {text}"
    try:
        data = r.json()
    except Exception as e:
        return None, f"json-error: {e}"
    posts = data.get("data", [])
    return posts, None

def extract_share_links_from_post(post):
    links = []
    body = post.get("body", "") or ""
    # search in body
    for m in SHARE_RE.findall(body):
        links.append(m.strip())
    # also inspect 'link' and 'embed' if present
    link_field = post.get("link")
    if link_field and isinstance(link_field, str):
        if "roblox.com/share" in link_field:
            links.append(link_field.strip())
    embed = post.get("embed")
    if embed and isinstance(embed, dict):
        url = embed.get("url") or embed.get("imageUrl")
        if url and "roblox.com/share" in url:
            links.append(url.strip())
    return list(dict.fromkeys(links))

@client.event
async def on_ready():
    print("Logged in as", client.user)
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("✅ Bot started successfully and is now monitoring the group wall!")
        except Exception as e:
            print("Startup message failed:", e)
    else:
        print("Channel not found at startup. Check CHANNEL_ID and bot permissions.")
    await monitor_loop()

async def monitor_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found. Exiting monitor loop.")
        return
    while not client.is_closed():
        posts, err = fetch_group_posts()
        if err:
            print("Fetch error:", err)
        else:
            found_links = []
            for p in posts:
                post_id = str(p.get("id") or p.get("postId") or "")
                links = extract_share_links_from_post(p)
                for link in links:
                    key = f"{post_id}|{link}"
                    if key not in sent:
                        sent.add(key)
                        found_links.append(link)
            if found_links:
                chunk = found_links[:20]
                try:
                    await channel.send("\n".join(chunk))
                    print(f"Sent {len(chunk)} new links to channel.")
                except Exception as e:
                    print("Failed to send message:", e)
            else:
                print("No new share links found this round.")
        await asyncio.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    client.run(TOKEN)
