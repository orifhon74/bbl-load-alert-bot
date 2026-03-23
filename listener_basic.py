import os
import re
from telethon import TelegramClient, events
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

CHANNEL_ID_RAW = os.getenv("CHANNEL_ID")
if not CHANNEL_ID_RAW:
    raise RuntimeError("Missing CHANNEL_ID in .env")

try:
    TARGET_CHAT = int(CHANNEL_ID_RAW)
except ValueError:
    raise RuntimeError("CHANNEL_ID must be an integer")

SESSION_PATH = os.getenv("SESSION_PATH", "./listener_session")
client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

STOP_RE = re.compile(r"Stop\s+\d+:\s*(.+)", re.IGNORECASE)
CITY_STATE_RE = re.compile(r"([A-Z][A-Z\s\.\'-]+?),\s*([A-Z]{2}),\s*USA\b", re.IGNORECASE)


def parse_stops(text: str):
    stop_lines = STOP_RE.findall(text or "")
    if len(stop_lines) < 2:
        return []

    stops = []
    for line in stop_lines:
        line = line.strip().upper()
        m = CITY_STATE_RE.search(line)
        if m:
            city = m.group(1).strip().upper()
            state = m.group(2).strip().upper()
            stops.append((city, state))

    return stops if len(stops) >= 2 else []


@client.on(events.NewMessage(chats=TARGET_CHAT))
async def on_new_message(event):
    text = event.raw_text or ""
    stops = parse_stops(text)

    if not stops:
        return

    print("\n=== NEW LOAD ===")
    for i, (city, st) in enumerate(stops, 1):
        print(f"Stop {i}: {city.title()}, {st}")


async def main():
    print(f"Listening to {TARGET_CHAT} ...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.start()
    client.loop.run_until_complete(main())