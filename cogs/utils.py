import discord
import psycopg2
import os

async def send_log(bot, message: str):
    log_channel_id = bot.settings.get("log_channel_id")

    if not log_channel_id:
        print(f"[LOG] {message}")
        return
    log_channel_id = int(log_channel_id)

    channel = bot.get_channel(log_channel_id)
    if channel is None:
        print(f"[LOG] (Channel not found) {message}")
        return
    
    try:
        await channel.send(message)
    except Exception as e:
        print(f"[LOG ERROR] Unable to send message to log channel: {e}")

def get_spam_messages() -> list[str]:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT content FROM spam_messages")
            return [row[0] for row in cur.fetchall()]