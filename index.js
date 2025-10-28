const { Client, GatewayIntentBits, EmbedBuilder } = require("discord.js");
const fetch = require("node-fetch");
require("dotenv").config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

const GROUP_ID = "35815907"; // Brazilian Spyder group
const CHANNEL_ID = process.env.CHANNEL_ID;

async function fetchLinks() {
  try {
    const res = await fetch(`https://groups.roblox.com/v2/groups/${GROUP_ID}/wall/posts?limit=20`);
    const data = await res.json();

    let links = [];
    for (const post of data.data) {
      const found = post.body.match(/https?:\/\/[^\s]+/g);
      if (found) links.push(...found);
    }

    links = [...new Set(links)];
    return links;
  } catch (err) {
    console.error("Error fetching Roblox links:", err);
    return [];
  }
}

async function sendEmbed() {
  const channel = client.channels.cache.get(CHANNEL_ID);
  if (!channel) return;

  const links = await fetchLinks();
  if (links.length === 0) return;

  const embed = new EmbedBuilder()
    .setTitle("🔗 Latest Roblox Links from Group Wall")
    .setDescription(links.join("\n"))
    .setColor(0x00ff99)
    .setFooter({ text: "Made By SAB-RS" });

  await channel.send({ embeds: [embed] });
  console.log(`✅ Sent ${links.length} links.`);
}

client.once("ready", () => {
  console.log(`🤖 Logged in as ${client.user.tag}`);
  sendEmbed();
  setInterval(sendEmbed, 60 * 1000); // every 1 minute
});

client.login(process.env.TOKEN);
