import discord
from discord.ext import commands, tasks
from discord import app_commands
import tweepy
import os
from web import keep_alive  # Flask server to keep the bot alive

# ENV
TOKEN = os.environ['DISCORD_BOT_TOKEN']
GUILD_ID = int(os.environ['DISCORD_GUILD_ID'])
ROLE_ID = int(os.environ['MENTION_ROLE_ID'])
CHANNEL_ID = int(os.environ['TWITTER_CHANNEL_ID'])
TWITTER_BEARER_TOKEN = os.environ['TWITTER_BEARER_TOKEN']
TWITTER_USER_ID = os.environ['TWITTER_USER_ID']

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
last_tweet_id = None

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton())

class TicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎫 Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")

    async def callback(self, interaction: discord.Interaction):
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
        }
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}", overwrites=overwrites)
        await channel.send(f"{interaction.user.mention}, ticket created.")
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

@bot.tree.command(name="announce", description="Send announcement with ticket button")
@app_commands.describe(message="Announcement content")
async def announce(interaction: discord.Interaction, message: str):
    await interaction.channel.send(f"📢 {message}", view=TicketView())
    await interaction.response.send_message("✅ Announcement sent", ephemeral=True)

@bot.tree.command(name="ticketpanel", description="Send ticket button panel")
async def ticketpanel(interaction: discord.Interaction):
    await interaction.response.send_message("Click below to create a ticket:", view=TicketView())

@tasks.loop(seconds=60)
async def check_twitter():
    global last_tweet_id
    try:
        tweets = twitter_client.get_users_tweets(id=TWITTER_USER_ID, max_results=5)
        if tweets.data:
            latest = tweets.data[0]
            if latest.id != last_tweet_id:
                last_tweet_id = latest.id
                tweet_url = f"https://x.com/i/web/status/{latest.id}"
                channel = bot.get_channel(CHANNEL_ID)
                await channel.send(f"<@&{ROLE_ID}> New tweet: {tweet_url}")
    except Exception as e:
        print("Twitter check error:", e)

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    check_twitter.start()
    print(f"✅ Logged in as {bot.user}")

# Keep alive with Flask
keep_alive()
bot.run(TOKEN)
