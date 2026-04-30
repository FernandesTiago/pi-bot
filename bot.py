# Pi Telegram Bot — system monitoring + remote commands.
# Run via systemd. Authenticated to a single user.

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import configparser
import logging
import psutil
import socket
import subprocess
import time
from functools import wraps
from pathlib import Path

# ---------- CONFIG ---------- 

BASE_DIR = Path(__file__).parent

config = configparser.ConfigParser()
config.read(BASE_DIR / "config.ini")

TOKEN = config["credentials"]["TELEGRAM_BOT_TOKEN"]
USER_ID = int(config["credentials"]["TELEGRAM_USER_ID"])

# Services to check with /services — adjust to your setup
MONITORED_SERVICES = ["pihole-FTL", "wg-quick@wg0", "ssh"]

# ---------- LOGGING ---------- 

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# Silence noisy libs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

log = logging.getLogger(__name__)


# ---------- AUTH ---------- 

def restricted(func):
    """Block any user other than USER_ID. Logs unauthorized attempts."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if update.effective_chat.id != USER_ID:
            log.warning(
                f"Unauthorized: id={user.id} username={user.username} "
                f"cmd={update.message.text if update.message else '?'}"
            )
            return
        log.info(f"cmd={update.message.text} from={user.username or user.id}")
        return await func(update, context)
    return wrapper


# ---------- HELPERS ---------- 

def format_uptime(seconds: int) -> str:
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m"


def get_temp() -> str:
    try:
        temp = psutil.sensors_temperatures()["cpu_thermal"][0].current
        return f"{temp:.1f}°C"
    except (KeyError, AttributeError, IndexError):
        return "N/A"


def get_ips() -> dict:
    """Return dict of interface_name -> ip for relevant interfaces."""
    result = {}
    for iface, addrs in psutil.net_if_addrs().items():
        if iface == "lo":
            continue
        for addr in addrs:
            if addr.family == socket.AF_INET:
                result[iface] = addr.address
    return result

# ---------- COMMANDS ---------- 

@restricted
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥧 Pi bot online.\n"
        "Type /help to see available commands."
    )


@restricted
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*Available commands:*\n"
        "/stats — CPU, RAM, disk, temp\n"
        "/temp — temperature only\n"
        "/disk — all mounted partitions\n"
        "/uptime — system uptime\n"
        "/services — status of critical services\n"
        "/ip — Pi IP addresses\n"
        "/speedtest — run speedtest (takes ~30s)\n"
        "/ping — health check\n"
        "/help — this message"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@restricted
async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")


@restricted
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    temp = get_temp()

    text = (
        f"🖥 *Pi Stats*\n"
        f"```\n"
        f"CPU : {cpu:5.1f}%   {temp}\n"
        f"RAM : {ram.used/1024**3:5.2f} / {ram.total/1024**3:.2f} GB ({ram.percent}%)\n"
        f"Disk: {disk.used/1024**3:5.2f} / {disk.total/1024**3:.2f} GB ({disk.percent}%)\n"
        f"```"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@restricted
async def cmd_temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🌡 Temp: {get_temp()}")


@restricted
async def cmd_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["💾 *Disk Usage*", "```"]
    for part in psutil.disk_partitions(all=False):
        # Skip pseudo filesystems
        if part.fstype in ("", "squashfs", "tmpfs", "devtmpfs"):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            lines.append(
                f"{part.mountpoint:15} "
                f"{usage.used/1024**3:6.1f} / {usage.total/1024**3:6.1f} GB "
                f"({usage.percent}%)"
            )
        except PermissionError:
            continue
    lines.append("```")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@restricted
async def cmd_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    seconds = int(time.time() - psutil.boot_time())
    await update.message.reply_text(f"⏱ Uptime: {format_uptime(seconds)}")


@restricted
async def cmd_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🔧 *Services*", "```"]
    for svc in MONITORED_SERVICES:
        result = subprocess.run(
            ["systemctl", "is-active", svc],
            capture_output=True, text=True
        )
        status = result.stdout.strip()
        icon = "✅" if status == "active" else "❌"
        lines.append(f"{icon} {svc:25} {status}")
    lines.append("```")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@restricted
async def cmd_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ips = get_ips()
    lines = ["🌐 *IP Addresses*", "```"]
    for iface, ip in ips.items():
        lines.append(f"{iface:10} {ip}")
    lines.append("```")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@restricted
async def cmd_speedtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Running speedtest, hold on...")
    
    from speedtest_runner import SpeedTest
    
    try:
        runner = SpeedTest()
        result = runner.run()
        if result["success"]:
            text = (
                f"✅ *Speedtest Results*\n"
                f"```\n"
                f"Down  : {result['download']:.2f} Mbps\n"
                f"Up    : {result['upload']:.2f} Mbps\n"
                f"Ping  : {result['ping']:.1f} ms\n"
                f"Server: {result['server']}\n"
                f"```"
            )
        else:
            text = f"❌ Speedtest failed: `{result['error']}`"
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        log.exception("Speedtest command failed")
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode="Markdown")

# ---------- ERROR HANDLER ---------- 

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Exception in handler:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ Internal error: `{context.error}`",
                parse_mode="Markdown",
            )
        except Exception:
            pass  # If we can't even send the error message, just log it



# ---------- MAIN ---------- 


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    handlers = [
        ("start", cmd_start),
        ("help", cmd_help),
        ("ping", cmd_ping),
        ("stats", cmd_stats),
        ("temp", cmd_temp),
        ("disk", cmd_disk),
        ("uptime", cmd_uptime),
        ("services", cmd_services),
        ("ip", cmd_ip),
        ("speedtest", cmd_speedtest),
    ]
    for cmd, fn in handlers:
        application.add_handler(CommandHandler(cmd, fn))

    application.add_error_handler(error_handler)

    log.info("Bot starting...")
    application.run_polling()


if __name__ == "__main__":
    main()