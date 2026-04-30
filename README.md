# Pi-Bot

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

Personal Telegram bot for my Raspberry Pi 5 home server. Monitors system health, runs scheduled speedtests, and serves as a central dashboard for all Pi services — all controllable from my phone.

## Features

**System monitoring**
- `/stats` — CPU, RAM, disk, and temperature
- `/temp` — temperature only (quick check)
- `/disk` — usage across all mounted partitions
- `/uptime` — system uptime, formatted
- `/ip` — IP addresses on every active interface

**Service health**
- `/services` — status of critical services (Pi-hole, WireGuard, SSH, etc)

**Speedtest**
- `/speedtest` — run an on-demand test and return download/upload/ping
- Scheduled tests via cron, results logged to SQLite for historical analysis

**Misc**
- `/ping` — health check
- `/help` — list all available commands
- Single-user authentication (only the configured Telegram ID can interact)
- All exceptions logged via `journalctl`; errors also surface in Telegram

## Stack

- **Hardware:** Raspberry Pi 5 8GB (headless, ethernet, 24/7)
- **Language:** Python 3
- **Bot framework:** python-telegram-bot
- **System metrics:** psutil
- **Speedtest engine:** Ookla speedtest CLI
- **Database:** SQLite
- **Scheduling:** cron (speedtests) + systemd (bot)
- **Future:** Grafana dashboards reading from the SQLite DB

## Repo structure

```
pi-bot/
├── bot.py              Main bot script (Telegram handlers)
├── speedtest.py        Speedtest runner (cron + /speedtest command)
├── config.ini          Credentials — not tracked by Git
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
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Ookla speedtest CLI (system-wide)
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt install speedtest
speedtest  # accept license interactively, once

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
TELEGRAM_USER_ID = your-chat-id
```

Get your bot token from [@BotFather](https://t.me/BotFather) and your user ID from [@userinfobot](https://t.me/userinfobot).

## Running 24/7 (systemd)

```ini
# /etc/systemd/system/telegram-bot.service
[Unit]
Description=Pi Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/pi-bot
ExecStart=/home/youruser/pi-bot/.venv/bin/python /home/youruser/pi-bot/bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-bot
journalctl -u telegram-bot -f
```

## Scheduled speedtests

Cron schedule (weekdays + early morning, off-peak hours to avoid interfering with home network use):

```cron
0 2,4,6 * * *   /home/youruser/pi-bot/.venv/bin/python /home/youruser/pi-bot/speedtest.py
0 14,16 * * 1-5 /home/youruser/pi-bot/.venv/bin/python /home/youruser/pi-bot/speedtest.py
```

Results are stored in `SpeedTestDB.db` and can be queried via `sqlite3` or visualized later in Grafana.

## Roadmap

- [x] Phase 1 — system monitoring (`/stats`, `/temp`, `/disk`, `/uptime`, `/ip`)
- [x] Phase 2 — speedtest integration (`/speedtest` + cron + SQLite)
- [x] Phase 3 — service health (`/services`)
- [ ] Phase 4 — admin commands (restart services, show external IP)
- [ ] Phase 5 — automated alerts (low speed, service down, reboot detection)
- [ ] Grafana dashboards reading from the SQLite DB
