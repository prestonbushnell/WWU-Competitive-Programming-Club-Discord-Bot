import discord
from discord.ext import commands
import logging
import json, os, asyncio
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Always use the directory where this script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Role Reaction Setup
VERIFY_MESSAGE_ID = None 
ROLE_ID = None
EMOJI = None

# Load settings
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

# Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("DISCORD_TOKEN is not set in the .env file.")
settings = load_settings()

# Logging setup
handler = logging.FileHandler(
    filename=os.path.join(BASE_DIR, "discord.log"),
    encoding='utf-8',
    mode='w'
)

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.event
async def on_member_join(member):
    # Auto-kick accounts newer than 7 days
    account_age = datetime.now(timezone.utc) - member.created_at
    if account_age < timedelta(days=7):
        try:
            await member.kick(reason="Account too new.")
            print(f"Kicked suspicious account {member}")
        except discord.Forbidden:
            print(f"Failed to kick account {member}")
    # DM welcome message
    try:
        await member.send(
            "Welcome to the WWU Competitive Programming Club Server! Please make sure to check out <#947639896292606016> and click the ✅ to gain access to the rest of the server."
        )
        print(f"Sent a welcome DM to {member.name}")
    except discord.Forbidden:
        print(f"Unable to DM {member.name}")
    
@bot.event
async def on_raw_reaction_add(payload):
    # Ignore the bot’s own reactions
    if payload.user_id == bot.user.id:
        return

    role_id = settings.get("role_id")
    message_id = settings.get("verify_message_id")
    emoji = settings.get("emoji", "✅")

    # Ensure config is set and matches
    if not role_id or not message_id:
        return
    if payload.message_id != message_id or str(payload.emoji) != emoji:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    try:
        # Always fetch the correct reacting member directly from Discord
        member = await guild.fetch_member(payload.user_id)

        # Make sure the role exists
        role = guild.get_role(role_id)
        if role is None:
            print("Role not found — check your stored role ID.")
            return

        await member.add_roles(role, reason="User verified via reaction")
        print(f"✅ Assigned {role.name} to {member.display_name}")
    except discord.Forbidden:
        print("❌ Missing permissions to assign role.")
    except discord.NotFound:
        print("❌ Member not found (might have left).")
    except Exception as e:
        print(f"⚠️ Error assigning role: {e}")
                
# Set Role to be given after reaction
@discord.app_commands.command(name="set_verify_role", description="Set the role to assign when users react to verify.")
@commands.has_permissions(administrator=True)
async def set_verify_role(interaction: discord.Interaction, role: discord.Role):
    settings["role_id"] = role.id
    save_settings(settings)
    await interaction.response.send_message(f"Verification role updated to {role.mention}", ephemeral=True)

# Set ID of Message to react to for verification
@discord.app_commands.command(name="set_verify_message", description="Set the message users should react to for verification.")
@commands.has_permissions(administrator=True)
async def set_verify_message(interaction: discord.Interaction, message_id: str):
    settings["verify_message_id"] = int(message_id)
    save_settings(settings)

    # Attempt to react to the message with the configured emoji
    emoji = settings.get("emoji", "✅")
    try:
        channel = interaction.channel
        message = await channel.fetch_message(int(message_id))
        await message.add_reaction(emoji)
        await interaction.response.send_message(
            f"Verification message set to {message.jump_url} and reacted with {emoji}",
            ephemeral=True
        )
        print(f"Added {emoji} reaction to verification message {message_id}")
    except Exception as e:
        await interaction.response.send_message(
            f"Verification message ID set to {message_id}, but failed to add reaction: {e}",
            ephemeral=True
        )
        print(f"Failed to react to message {message_id}: {e}")

# Set Emoji to be used for verification reaction
@discord.app_commands.command(name="set_verify_emoji", description="Set the emoji users should react with for verification.")
@commands.has_permissions(administrator=True)
async def set_verify_emoji(interaction: discord.Interaction, emoji: str):
    settings["emoji"] = emoji
    save_settings(settings)
    await interaction.response.send_message(f"Verification emoji set to {emoji}", ephemeral=True)

# Reset bot on server side
@discord.app_commands.command(name="restart_bot", description="Restart the bot service on the server.")
@commands.has_permissions(administrator=True)
async def restart_bot(interaction: discord.Interaction):
    user = interaction.user

    # Respond privately so others can't see
    await interaction.response.send_message(
        f"Restarting bot...", ephemeral=True
    )
    print(f"Bot restart requested by {user.name} ({user.id})")

    # Give Discord time to send the response before shutting down
    await asyncio.sleep(2)

    # Restart the systemd service
    os.system("sudo systemctl restart discordbot")
    
@bot.event
async def setup_hook():
    bot.tree.add_command(set_verify_role)
    bot.tree.add_command(set_verify_message)
    bot.tree.add_command(set_verify_emoji)
    bot.tree.add_command(restart_bot)
    await bot.tree.sync(guild=discord.Object(id=947639896292606013))
    print("Slash commands synced")

# Run the bot
bot.run(token, log_handler=handler, log_level=logging.INFO)