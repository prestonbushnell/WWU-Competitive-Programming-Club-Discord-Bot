import discord

async def send_log(bot, message: str):
    log_channel_id = bot.settings.get("log_channel_id")

    if not log_channel_id:
        print(f"[LOG] {message}")
        return

    channel = bot.get_channel(log_channel_id)
    if channel is None:
        print(f"[LOG] (Channel not found) {message}")
        return
    
    try:
        await channel.send(message)
    except Exception as e:
        print(f"[LOG ERROR] Unable to send message to log channel: {e}")