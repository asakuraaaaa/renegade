import discord
from discord.ext import commands, tasks
from discord import app_commands
import tweepy
import os
import asyncio

# Environment Variables
DISCORD_TOKEN = os.environ['MTE2MDU1NDExODY1NDQ2MDAzNg.GZXMHg.k03m7PNY2TLclyOwWXmJv09jdr5Wic8l5yiWvk']
GUILD_ID = int(os.environ['890645770133463061D'])
ROLE_ID = int(os.environ['1052479555681652746'])
CHANNEL_ID = int(os.environ['1376957766945476779D'])
TWITTER_BEARER_TOKEN = os.environ['AAAAAAAAAAAAAAAAAAAAAAU32AEAAAAAuDmW0Z14qBhHvPTBxFASxBDVfcA%3D6koN05f0wMerHXBlWZdVGx7h4xmie345DpsW7gpxjq44BWkWHoN']
TWITTER_USER_ID = os.environ['1927399974037319680']  # Numeric user ID, not @handle

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Twitter setup
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
last_tweet_id = None

# ====================== TICKET BUTTONS ======================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton())

class TicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
        }
        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            reason="Support Ticket"
        )
        await channel.send(f"{interaction.user.mention}, thank you! A staff member will assist you soon.")
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# ====================== SLASH COMMANDS ======================

@bot.tree.command(name="announce", description="Send an announcement with a button")
@app_commands.describe(message="Message to send")
async def announce(interaction: discord.Interaction, message: str):
    view = TicketView()
    await interaction.channel.send(f"📢 {message}", view=view)
    await interaction.response.send_message("✅ Announcement sent!", ephemeral=True)

@bot.tree.command(name="ticketpanel", description="Send a ticket creation panel")
async def ticketpanel(interaction: discord.Interaction):
    view = TicketView()
    await interaction.response.send_message("Click below to create a ticket:", view=view)

# ====================== TWITTER CHECK ======================

@tasks.loop(seconds=60)
async def check_twitter():
    global last_tweet_id
    try:
        tweets = twitter_client.get_users_tweets(
            id=TWITTER_USER_ID, max_results=5, tweet_fields=["created_at"]
        )

        if tweets.data:
            latest = tweets.data[0]
            if latest.id != last_tweet_id:
                last_tweet_id = latest.id
                tweet_url = f"https://x.com/i/web/status/{latest.id}"
                channel = bot.get_channel(CHANNEL_ID)
                await channel.send(f"<@&{ROLE_ID}> New tweet: {tweet_url}")
    except Exception as e:
        print(f"❌ Twitter check error: {e}")

# ====================== READY EVENT ======================

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot is ready. Logged in as {bot.user}")
    check_twitter.start()

bot.run(DISCORD_TOKEN)
