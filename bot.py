import os
import threading
import asyncio
import logging

import discord
from discord.ext import commands
from flask import Flask, request, redirect, url_for, session

# ============================================================
# CONFIG
# ============================================================

TOKEN = os.environ.get("TOKEN")
DASH_KEY = os.environ.get("DASH_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")

PREFIX = "!"

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)

log = logging.getLogger("genga-bot")

# ============================================================
# VALIDATE ENVIRONMENT
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "TOKEN environment variable is missing. "
        "Add TOKEN in Render Environment Variables."
    )

if not DASH_KEY:
    raise RuntimeError(
        "DASH_KEY environment variable is missing."
    )

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is missing."
    )

# ============================================================
# DISCORD
# ============================================================

intents = discord.Intents.default()

# Required for commands that read message content
intents.message_content = True

# Required for member counts/member information
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents
)

# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ============================================================
# DISCORD EVENTS
# ============================================================

@bot.event
async def on_ready():
    log.info("========================================")
    log.info("DISCORD BOT ONLINE")
    log.info("User: %s", bot.user)
    log.info("ID: %s", bot.user.id)
    log.info("Servers: %s", len(bot.guilds))

    for guild in bot.guilds:
        log.info(
            "Guild: %s | ID: %s | Members: %s",
            guild.name,
            guild.id,
            guild.member_count
        )

    log.info("========================================")


@bot.event
async def on_disconnect():
    log.warning("Discord connection lost.")


@bot.event
async def on_resumed():
    log.info("Discord connection resumed.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You don't have permission to use this command.",
            delete_after=5
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "❌ Missing required argument.",
            delete_after=5
        )
        return

    log.exception("Command error:", exc_info=error)

    try:
        await ctx.send(
            "❌ An error occurred while executing the command.",
            delete_after=5
        )
    except Exception:
        pass


# ============================================================
# SAFE TEST COMMANDS
# ============================================================

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)

    await ctx.send(
        f"🏓 Pong! `{latency} ms`"
    )


@bot.command(name="Start")
@commands.has_permissions(administrator=True)
async def start(ctx):
    """
    Safe replacement for the old destructive !Start command.
    It only confirms that the bot is operational.
    """

    await ctx.send(
        "✅ Bot is online and responding correctly."
    )


@bot.command(name="server")
@commands.has_permissions(administrator=True)
async def server_info(ctx):
    guild = ctx.guild

    if guild is None:
        await ctx.send("❌ This command must be used inside a server.")
        return

    await ctx.send(
        f"**Server Information**\n"
        f"Name: `{guild.name}`\n"
        f"ID: `{guild.id}`\n"
        f"Members: `{guild.member_count}`\n"
        f"Channels: `{len(guild.channels)}`\n"
        f"Roles: `{len(guild.roles)}`"
    )


# ============================================================
# AUTH
# ============================================================

def logged_in():
    return session.get("auth") is True


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        key = request.form.get("key", "")

        if key == DASH_KEY:
            session["auth"] = True
            return redirect(url_for("index"))

        return """
        <!DOCTYPE html>
        <html>
        <body style="
            background:#111;
            color:#eee;
            font-family:monospace;
            padding:30px;
        ">
            <h2>Invalid dashboard key</h2>
            <a href="/login" style="color:#8ab4ff">
                Try again
            </a>
        </body>
        </html>
        """, 403

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>Bot Login</title>
    </head>

    <body style="
        background:#111;
        color:#eee;
        font-family:monospace;
        padding:30px;
    ">

        <h2>Bot Dashboard</h2>

        <form method="post">

            <input
                name="key"
                type="password"
                placeholder="Dashboard Key"
                autofocus
                style="
                    padding:10px;
                    background:#222;
                    color:#fff;
                    border:1px solid #555;
                "
            >

            <button
                type="submit"
                style="
                    padding:10px 18px;
                    margin-left:5px;
                    cursor:pointer;
                "
            >
                Login
            </button>

        </form>

    </body>
    </html>
    """


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def index():

    if not logged_in():
        return redirect(url_for("login"))

    connected = bot.is_ready()

    bot_name = str(bot.user) if bot.user else "Not connected"

    rows = ""

    for guild in bot.guilds:

        rows += f"""
        <tr>
            <td>{guild.name}</td>
            <td>{guild.id}</td>
            <td>{guild.member_count}</td>
            <td>
                <a href="/server/{guild.id}">
                    Open
                </a>
            </td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="4">
                Bot is not connected to any servers.
            </td>
        </tr>
        """

    status_color = "#35d07f" if connected else "#ff5555"

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta
            name="viewport"
            content="width=device-width,initial-scale=1"
        >

        <title>Bot Dashboard</title>

        <style>

            body {{
                background:#111;
                color:#eee;
                font-family:monospace;
                padding:20px;
            }}

            table {{
                border-collapse:collapse;
                width:100%;
                max-width:900px;
            }}

            th, td {{
                border:1px solid #444;
                padding:10px;
                text-align:left;
            }}

            th {{
                background:#222;
            }}

            a {{
                color:#8ab4ff;
            }}

            .status {{
                color:{status_color};
                font-weight:bold;
            }}

        </style>

    </head>

    <body>

        <h2>Bot Dashboard</h2>

        <p>
            Logged in as:
            <strong>{bot_name}</strong>
        </p>

        <p>
            Discord status:
            <span class="status">
                {"ONLINE" if connected else "OFFLINE"}
            </span>
        </p>

        <p>
            Servers:
            <strong>{len(bot.guilds)}</strong>
        </p>

        <p>
            <a href="/health">Health</a>
            |
            <a href="/logout">Logout</a>
        </p>

        <table>

            <tr>
                <th>Server</th>
                <th>ID</th>
                <th>Members</th>
                <th>Action</th>
            </tr>

            {rows}

        </table>

    </body>

    </html>
    """


# ============================================================
# SERVER INFORMATION
# ============================================================

@app.route("/server/<int:guild_id>")
def server(guild_id):

    if not logged_in():
        return redirect(url_for("login"))

    guild = bot.get_guild(guild_id)

    if guild is None:
        return "Guild not found", 404

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta
            name="viewport"
            content="width=device-width,initial-scale=1"
        >

        <title>{guild.name}</title>

    </head>

    <body style="
        background:#111;
        color:#eee;
        font-family:monospace;
        padding:20px;
    ">

        <h2>{guild.name}</h2>

        <hr>

        <p>
            <strong>ID:</strong>
            {guild.id}
        </p>

        <p>
            <strong>Members:</strong>
            {guild.member_count}
        </p>

        <p>
            <strong>Channels:</strong>
            {len(guild.channels)}
        </p>

        <p>
            <strong>Roles:</strong>
            {len(guild.roles)}
        </p>

        <p>
            <strong>Owner:</strong>
            {guild.owner}
        </p>

        <hr>

        <h3>Bot Status</h3>

        <p>
            Connected:
            {"YES" if bot.is_ready() else "NO"}
        </p>

        <p>
            <a href="/">← Back</a>
        </p>

    </body>

    </html>
    """


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    discord_status = bot.is_ready()

    return {
        "flask": "ok",
        "discord": "online" if discord_status else "offline",
        "bot": str(bot.user) if bot.user else None,
        "guilds": len(bot.guilds)
    }, 200


# ============================================================
# BOT THREAD
# ============================================================

def run_bot():

    try:

        log.info("Starting Discord bot...")

        bot.run(TOKEN)

    except discord.LoginFailure:

        log.error(
            "Discord login failed. "
            "Check the TOKEN environment variable."
        )

    except Exception:

        log.exception(
            "Discord bot crashed."
        )


# ============================================================
# FLASK THREAD / RENDER
# ============================================================

def run_flask():

    port = int(
        os.environ.get("PORT", "8080")
    )

    log.info(
        "Starting Flask on port %s",
        port
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    log.info("Starting application...")

    discord_thread = threading.Thread(
        target=run_bot,
        name="DiscordBot",
        daemon=True
    )

    discord_thread.start()

    run_flask()
