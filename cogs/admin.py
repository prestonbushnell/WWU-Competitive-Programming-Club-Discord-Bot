import discord
from discord.ext import commands
from discord import app_commands
import asyncio, os
from .utils import send_log

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Set server channel that bot will log to
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.command(name="set_log_channel", description="Set the channel for bot logs.")
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.bot.settings["log_channel_id"] = channel.id  # int in memory
        self.bot.save_settings(self.bot.settings)
        await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)

    # Restart the bot via server commands
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.command(name="restart_bot", description="Restart the bot service on the server.")
    async def restart_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message("Restarting bot...", ephemeral=True)
        await send_log(self.bot, f"Restart requested by {interaction.user} ({interaction.user.id})")
        await asyncio.sleep(2)
        result = os.system("sudo -n systemctl restart discordbot")

        if result != 0:
            await send_log(self.bot, f"Unable to restart. Exited with code {result}")
    
    # Send a test message to the previously defined logs channel
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.command(name="test_logs", description="Test the logging channel.")
    async def test_logs(self, interaction: discord.Interaction):
        await interaction.response.send_message("Sent test log!", ephemeral=True)
        await send_log(self.bot, "This is a test message")

async def setup(bot):
    await bot.add_cog(Admin(bot))
    
