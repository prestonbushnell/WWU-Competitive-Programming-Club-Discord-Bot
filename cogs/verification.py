import discord
from discord.ext import commands
from discord import app_commands
from typing import cast
from .utils import send_log
class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.command(name="set_verify_role", description="Set the role given when users verify.")
    async def set_verify_role(self, interaction: discord.Interaction, role: discord.Role):
        self.bot.settings["role_id"] = role.id
        self.bot.save_settings(self.bot.settings)
        await interaction.response.send_message(f"Verification role set to {role.mention}", ephemeral=True)

    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.command(name="set_verify_message", description="Set the message users should react to for verification.")
    async def set_verify_message(self, interaction: discord.Interaction, message_id: str):
        self.bot.settings["verify_message_id"] = int(message_id)
        self.bot.save_settings(self.bot.settings)
        emoji = self.bot.settings.get("emoji", "✅")
        try:
            channel = cast(discord.TextChannel | discord.Thread, interaction.channel)
            message = await channel.fetch_message(int(message_id))
            await message.add_reaction(emoji)
            await interaction.response.send_message(
                f"Verification message set to {message.jump_url} and reacted with {emoji}",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to react: {e}", ephemeral=True)

    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.command(name="set_verify_emoji", description="Set the emoji used for verification.")
    async def set_verify_emoji(self, interaction: discord.Interaction, emoji: str):
        self.bot.settings["emoji"] = emoji
        self.bot.save_settings(self.bot.settings)
        await interaction.response.send_message(f"Verification emoji set to {emoji}", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if self.bot.user and payload.user_id == self.bot.user.id:
            return
        role_id = self.bot.settings.get("role_id")
        message_id = self.bot.settings.get("verify_message_id")
        emoji = self.bot.settings.get("emoji", "✅")
        if not role_id or not message_id:
            return
        if payload.message_id != message_id or str(payload.emoji) != emoji:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        try:
            member = await guild.fetch_member(payload.user_id)
            role = guild.get_role(role_id)
            if not role:
                print("Role not found.")
                return
            await member.add_roles(role, reason="User verified via reaction")
            await send_log(self.bot, f"✅ Assigned {role.name} to {member.display_name}")
        except Exception as e:
            await send_log(self.bot, f"Error assigning role: {e}")

async def setup(bot):
    await bot.add_cog(Verification(bot))
