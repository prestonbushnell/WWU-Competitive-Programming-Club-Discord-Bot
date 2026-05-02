import discord
from discord.ext import commands
import logging, os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("DISCORD_TOKEN is not set in .env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Database helpers ──────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def load_settings() -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS spam_messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT UNIQUE NOT NULL,
                    added_by BIGINT,
                    added_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("SELECT key, value FROM settings")
            rows = cur.fetchall()
            return {row["key"]: row["value"] for row in rows}

def save_settings(data: dict):
    with get_db() as conn:
        with conn.cursor() as cur:
            for key, value in data.items():
                cur.execute("""
                    INSERT INTO settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """, (key, str(value)))

# ── Bot setup ─────────────────────────────────────────────────────────────────

handler = logging.FileHandler(
    filename=os.path.join(BASE_DIR, "discord.log"),
    encoding="utf-8",
    mode="w"
)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.settings = load_settings()
bot.save_settings = save_settings

@bot.event
async def setup_hook():
    guild = discord.Object(id=947639896292606013)

    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.verification")
    await bot.load_extension("cogs.welcome")

    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    print("Slash commands synced.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(token, log_handler=handler, log_level=logging.INFO)