import discord
from discord.ext import commands
from discord import app_commands
import asyncio, os, psycopg2
from .utils import send_log

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[DEBUG] Admin cog loaded")

    # Set server channel that bot will log to
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="set_log_channel", description="Set the channel for bot logs.")
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.bot.settings["log_channel_id"] = channel.id
        self.bot.save_settings(self.bot.settings)
        await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)

    # Restart the bot via server commands
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="restart_bot", description="Restart the bot service on the server.")
    async def restart_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message("Restarting bot...", ephemeral=True)
        await send_log(self.bot, f"Restart requested by {interaction.user} ({interaction.user.id})")
        await asyncio.sleep(2)
        result = os.system("sudo -n systemctl restart discordbot")

        if result != 0:
            await send_log(self.bot, f"Unable to restart. Exited with code {result}")

    # Send a test message to the previously defined logs channel
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="test_logs", description="Test the logging channel.")
    async def test_logs(self, interaction: discord.Interaction):
        await interaction.response.send_message("Sent test log!", ephemeral=True)
        await send_log(self.bot, "This is a test message")

    # Add a message to the spam database
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="add_spam", description="Add a message to the spam database.")
    async def add_spam(self, interaction: discord.Interaction, content: str):
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO spam_messages (content, added_by) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (content, interaction.user.id)
                )
        await interaction.response.send_message(f"Added to spam database: `{content[:100]}`", ephemeral=True)

    # Remove a message from the spam database
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="remove_spam", description="Remove a message from the spam database.")
    async def remove_spam(self, interaction: discord.Interaction, content: str):
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM spam_messages WHERE content = %s", (content,))
        await interaction.response.send_message(f"Removed from spam database: `{content[:100]}`", ephemeral=True)

    # List all known spam messages
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="list_spam", description="List all known spam messages.")
    async def list_spam(self, interaction: discord.Interaction):
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, content FROM spam_messages")
                rows = cur.fetchall()
        if not rows:
            await interaction.response.send_message("No spam messages in database.", ephemeral=True)
            return
        entries = "\n".join(f"`{row[0]}` — {row[1][:80]}" for row in rows)
        await interaction.response.send_message(f"**Spam messages:**\n{entries}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))