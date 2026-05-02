import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from .utils import send_log, get_spam_messages
from difflib import SequenceMatcher
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
                await send_log(self.bot, f"Kicked new account: {member.mention}")
                return
            except discord.Forbidden:
                await send_log(self.bot, f"Cannot kick {member.mention}")
        try:
            # TODO: Update to allow customization of channel ID
            await member.send(
                "Welcome to the WWU Competitive Programming Club! "
                "Please read <#947639896292606016> and click ✅ to verify."
            )
            await send_log(self.bot, f"DM sent to {member.mention}")
        except discord.Forbidden:
            await send_log(self.bot, f"Could not DM {member.mention} (DMs closed)")
        
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild

        # Check for bans
        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if log.target.id == member.id and (discord.utils.utcnow() - log.created_at).total_seconds() <= 3:
                moderator = log.user.mention if log.user else "Unknown Moderator"
                await send_log(self.bot, f"{member.mention} was banned by {moderator}.")
                return

        # Check for kicks
        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if log.target.id == member.id and (discord.utils.utcnow() - log.created_at).total_seconds() <= 3:
                moderator = log.user.mention if log.user else "Unknown Moderator"
                await send_log(self.bot, f"{member.mention} was kicked by {moderator}.")
                return

        # ----- Otherwise, they just left -----
        await send_log(self.bot, f"{member.mention} left the server.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        spam_list = get_spam_messages()
        for spam in spam_list:
            ratio = SequenceMatcher(None, message.content.lower(), spam.lower()).ratio()
            if ratio >= 0.85:
                try:
                    await message.delete()
                    await message.guild.ban(
                        message.author,
                        reason=f"Known Spam",
                        delete_message_seconds=604800
                    )
                    await send_log(
                        self.bot,
                        f"**Auto-banned** {message.author.mention} (`{message.author.id}`) for spam message in <#{message.channel.id}>\n"
                        f"**Matched:** `{spam[:100]}`\n"
                        f"**Similarity:** {ratio:.0%}"
                    )
                except discord.Forbidden:
                    await send_log(self.bot, f"Could not ban {message.author.mention} — missing permissions.")
                return

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Get the log channel ID from settings
        log_channel_id = self.bot.settings.get("log_channel_id")
        if not log_channel_id:
            return  # Logging not configured yet
        log_channel_id = int(log_channel_id)

        # Ignore deletes inside the log channel itself
        if message.channel.id == log_channel_id:
            return

        # Build log entry
        content = message.content or "*no text (possibly an embed or attachment)*"
        author = f"{message.author.mention} (`{message.author.id}`)"
        channel = f"<#{message.channel.id}>"

        log_text = (
            f"**Message Deleted**\n"
            f"**Author:** {author}\n"
            f"**Channel:** {channel}\n"
            f"**Content:**\n{content}"
        )

        await send_log(self.bot, log_text)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        # Skip if the message was cached — on_message_delete already handled it
        if payload.cached_message is not None:
            return

        log_channel_id = self.bot.settings.get("log_channel_id")
        if not log_channel_id:
            return
        log_channel_id = int(log_channel_id)

        if payload.channel_id == log_channel_id:
            return

        log_text = (
            f"**Message Deleted**\n"
            f"**Channel:** <#{payload.channel_id}>\n"
            f"**Message ID:** {payload.message_id}"
        )

        await send_log(self.bot, log_text)

async def setup(bot):
    await bot.add_cog(Welcome(bot))

def __init__(self, bot):
    self.bot = bot
    print("[DEBUG] Welcome cog loaded")