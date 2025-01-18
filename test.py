from pyrogram import Client, idle
from pytgcalls import PyTgCalls
from config import API_HASH , API_ID

client = Client("LandSession", api_id=API_ID,api_hash=API_HASH , phone_number="919878123956")

# Initialize PyTgCalls
app = PyTgCalls(client)

@client.on_message()
async def onMessage(_,message):
    print(message.text)

@client.on_raw_update()
async def handler(_, update, users, chats):
    print("Raw update received:", update)

async def main():
    await client.start()
    await app.start()
    print("Client and PyTgCalls started.")
    await client.send_message("me","Hello World")
    await idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())