import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from .utils import send_log
import asyncio

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        account_age = datetime.now(timezone.utc) - member.created_at
        if account_age < timedelta(days=7):
            try:
                await member.kick(reason="Account too new.")
                await send_log(self.bot, f"Kicked new account: {member}")
                return
            except discord.Forbidden:
                await send_log(self.bot, f"Cannot kick {member}")
        try:
            await member.send(
                "Welcome to the WWU Competitive Programming Club! "
                "Please read <#947639896292606016> and click ✅ to verify."
            )
            await send_log(self.bot, f"DM sent to {member.name}")
        except discord.Forbidden:
            await send_log(self.bot, f"Could not DM {member.name} (DMs closed)")
        
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        entry = None

        # Fetch the most recent kick log entry
        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            entry = log
            break

        # If there's no entry → leave
        if entry is None:
            await send_log(self.bot, f"{member} left the server.")
            return

        # If the entry is older than 3 seconds - leave
        if (discord.utils.utcnow() - entry.created_at).total_seconds() > 3:
            await send_log(self.bot, f"{member} left the server.")
            return

        # If the kick entry is NOT for this user - leave
        if entry.target.id != member.id: # type: ignore
            await send_log(self.bot, f"{member} left the server.")
            return

        # Otherwise - kick
        await send_log(
            self.bot,
            f"{member} was kicked by {entry.user}."
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Get the log channel ID from settings
        log_channel_id = self.bot.settings.get("log_channel_id")
        if not log_channel_id:
            return  # Logging not configured yet

        # Ignore deletes inside the log channel itself
        if message.channel.id == log_channel_id:
            return

        # Build log entry
        content = message.content or "*no text (possibly an embed or attachment)*"
        author = f"{message.author} (`{message.author.id}`)"
        channel = f"<#{message.channel.id}>"

        log_text = (
            f"**Message Deleted**\n"
            f"**Author:** <@{author}>\n"
            f"**Channel:** {channel}\n"
            f"**Content:**\n{content}"
        )

        await send_log(self.bot, log_text)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
