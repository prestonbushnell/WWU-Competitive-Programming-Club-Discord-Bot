import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("DISCORD_TOKEN is not set in the .env file.")

# Logging setup
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

# Example slash command
@discord.app_commands.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

@bot.event
async def setup_hook():
    bot.tree.add_command(hello)
    await bot.tree.sync()
    print("Slash commands synced")

# Run the bot
bot.run(token, log_handler=handler, log_level=logging.INFO)