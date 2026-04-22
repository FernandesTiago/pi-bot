# Pi-Bot ![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

Personal Telegram bot for my Raspberry Pi 5 home server. Monitors system health, runs scheduled speedtests, and serves as a central dashboard for all Pi services — all controllable from my phone.

## Currently building

**Phase 1** — Basic bot with `/ping`, `/status` (CPU, RAM, disk, uptime).

**Phase 2** — Speedtest integration: `/speed` (last test), `/average` (weekly average), `/history` (last 10 tests). Speedtest runs on a cron schedule and logs results to SQLite.

## Planned features

- **System monitoring:** CPU, RAM, disk, temperature, uptime
- **Speedtest tracker:** scheduled tests with historical data in SQLite
- **Service health:** check if Pi-hole, SAC bot, and other services are running
- **Admin commands:** restart services, show external IP
- **Automated alerts:** notify via Telegram when speed drops below threshold, services go down, or Pi reboots

## Stack

- **Hardware:** Raspberry Pi 5 8GB (headless, ethernet, 24/7)
- **Language:** Python 3
- **Bot framework:** python-telegram-bot
- **Database:** SQLite
- **Scheduling:** cron
- **Future:** Grafana dashboards reading from the SQLite DB

## Repo structure

```
pi-bot/
├── bot.py              # Main bot script (Telegram handlers)
├── speedtest_runner.py  # Speedtest script (runs via cron)
├── config.ini          # Credentials — not tracked by Git
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

```bash
# Clone and enter
git clone https://github.com/yourusername/pi-bot.git
cd pi-bot

# Create venv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and fill credentials
cp config.ini.example config.ini
nano config.ini

# Run
python bot.py
```

## Configuration

Create a `config.ini` with:

```ini
[credentials]
TELEGRAM_BOT_TOKEN = your-token-from-botfather
TELEGRAM_CHAT_ID = your-chat-id
```

Get your bot token from [@BotFather](https://t.me/BotFather) and your chat ID from [@userinfobot](https://t.me/userinfobot).

## Up next

- [ ] Phase 1: `/ping` and `/status` commands
- [ ] Phase 2: Speedtest logging + `/speed`, `/average`, `/history`
- [ ] Phase 3: `/services`, `/restart`, `/ip`
- [ ] Phase 4: Automated alerts via Telegram
- [ ] Grafana integration for speedtest visualization
