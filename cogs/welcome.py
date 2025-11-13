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
        
        await asyncio.sleep(1)

        guild = member.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target and entry.target.id == member.id:
                await send_log(self.bot, f"{member} was kicked by {entry.user}.")
                return

        # If not kicked or banned, treat as voluntary leave
        await send_log(self.bot, f"👋{member} left the server.")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
