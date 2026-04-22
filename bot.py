from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import configparser
from pathlib import Path
import psutil
import time

# ------------------------------
#         BASIC CONFIG
# ------------------------------

config = configparser.ConfigParser()
config.read(Path(__file__).parent / "config.ini")

TOKEN = config["credentials"]["TELEGRAM_BOT_TOKEN"]
USER_ID = int(config["credentials"]["TELEGRAM_USER_ID"])


# ------------------------------
#        AUTHENTICATION
# ------------------------------

def auth(update: Update) -> bool:
    return update.effective_chat.id == USER_ID

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="I'm a bot, please talk to me!"
    )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    try:
        temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
        temp_text = f"{temp}°C"
    except (KeyError, AttributeError, IndexError):
        temp_text = "N/A"
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    used_ram = ram.used / (1024**3)
    total_ram = ram.total / (1024**3)
    disk = psutil.disk_usage('/')
    used_disk = disk.used / (1024**3)
    total_disk = disk.total / (1024**3)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"CPU: {cpu}% | Temp: {temp_text}\n"
            f"RAM: Total: {total_ram:.2f}GB | Used: {used_ram:.2f}GB | ({ram.percent}%)\n"
            f"Disk: Total: {total_disk:.2f}GB | Used: {used_disk:.2f}GB | ({disk.percent}%)"
    ))

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Pong!"
        )
    
async def cmd_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    uptime = psutil.boot_time()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Uptime: {uptime}"
        )
    

if __name__ == '__main__':
    # Build the application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handler for /start command
    start_handler = CommandHandler('start', cmd_start)
    start_handler = CommandHandler('stats', cmd_stats)
    start_handler = CommandHandler('ping', cmd_ping)
    start_handler = CommandHandler('uptime', cmd_uptime)
    application.add_handler(start_handler)
    
    # Run the bot until you press Ctrl-C
    application.run_polling()