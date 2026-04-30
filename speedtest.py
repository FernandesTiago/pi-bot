import json
import logging
import sqlite3
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "SpeedTestDB.db"
LOG_PATH = BASE_DIR / "speedtest.log"

logging.basicConfig(
    filename=LOG_PATH,
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


class DataBase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS speed_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    download FLOAT,
                    upload FLOAT,
                    ping FLOAT,
                    server TEXT,
                    timestamp TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)

    def save(self, download, upload, ping, server):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO speed_logs (download, upload, ping, server) VALUES (?, ?, ?, ?)",
                (download, upload, ping, server),
            )
        log.info(f"Saved: {download} Mbps down, {upload} Mbps up, {ping} ms")


class SpeedTest:
    def __init__(self):
        self.db = DataBase()

    def run(self):
        log.info("Starting speedtest...")
        try:
            proc = subprocess.run(
                ["speedtest", "--format=json", "--accept-license", "--accept-gdpr"],
                capture_output=True,
                text=True,
                timeout=120,
                check=True,
            )
            data = json.loads(proc.stdout)

            # Ookla returns bandwidth in bytes/sec; multiply by 8 for bits/sec, divide by 1M for Mbps
            download = round(data["download"]["bandwidth"] * 8 / 1_000_000, 2)
            upload = round(data["upload"]["bandwidth"] * 8 / 1_000_000, 2)
            ping = round(data["ping"]["latency"], 1)
            server = f"{data['server']['name']} ({data['server']['location']})"

            self.db.save(download, upload, ping, server)

            return {
                "success": True,
                "download": download,
                "upload": upload,
                "ping": ping,
                "server": server,
            }

        except subprocess.TimeoutExpired:
            error = "Speedtest timed out after 120s"
            log.error(error)
            self.db.save(0.0, 0.0, 0.0, f"OUTAGE: {error}")
            return {"success": False, "error": error}

        except subprocess.CalledProcessError as e:
            error = f"Speedtest CLI failed: {e.stderr.strip()}"
            log.error(error)
            self.db.save(0.0, 0.0, 0.0, f"OUTAGE: {error}")
            return {"success": False, "error": error}

        except (json.JSONDecodeError, KeyError) as e:
            error = f"Failed to parse speedtest output: {e}"
            log.error(error)
            self.db.save(0.0, 0.0, 0.0, f"OUTAGE: {error}")
            return {"success": False, "error": error}


if __name__ == "__main__":
    runner = SpeedTest()
    result = runner.run()
    if result["success"]:
        print(f"Down: {result['download']} Mbps | Up: {result['upload']} Mbps | Ping: {result['ping']} ms | {result['server']}")
    else:
        print(f"Failed: {result['error']}")