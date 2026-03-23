import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_PATH = os.getenv("SESSION_PATH", "./bbl_listener_session_inspect")

async def main():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        print(f"NAME: {dialog.name}")
        print(f"ID: {entity.id}")
        print(f"USERNAME: {getattr(entity, 'username', None)}")
        print(f"ENTITY TYPE: {type(entity).__name__}")
        print("-" * 50)

    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())