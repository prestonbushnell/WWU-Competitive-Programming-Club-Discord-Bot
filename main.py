import discord
from discord.ext import commands
import logging, os, json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({}, f)
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("DISCORD_TOKEN is not set in .env")

settings = load_settings()

handler = logging.FileHandler(
    filename=os.path.join(BASE_DIR, "discord.log"),
    encoding="utf-8",
    mode="w"
)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.settings = settings  # type: ignore
bot.save_settings = save_settings  # type: ignore

@bot.event
async def setup_hook():
    guild = discord.Object(id=947639896292606013)

    # Load cogs 
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.verification")
    await bot.load_extension("cogs.welcome")

    await bot.tree.sync(guild=guild)
    print(f"Slash commands synced.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(token, log_handler=handler, log_level=logging.INFO)
