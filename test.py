from pyrogram import Client, idle
from pytgcalls import PyTgCalls

# Your session string
sessionString = "BQAx4pMATh-f0ovlqgNCTjA-pSBW6duTkqce8zM7VtEn8ObuX7L56rE6DmOXpvH62fH9ezpxaDS9u3GAG_UgOyZn_NpCsvPrO3cH_SAa2bAoefonLOWvq6-ywZWDl0gyLggdaKf7mL4DrBv6Z1sTMw07KsnDJZp5yv360JRwMV1cZf8EvKoBu3PB0YpIiD0mEuXbgfHbdu7eR-Is3Oe2Wr7ZqC7miZc82TjSkzC0qinmjgpjNMiBOZJTtJsh4T0vg8LkitALPqpkRM_T49h_u4fU4T9VmCsqtoPe4nxrgBZ2YwVf9TmNKdIW-WxowpUyL7cGjP-0tAWRjDOEyMh6L3dYSpqWYQAAAABXhc0CAA"

# Initialize Pyrogram Client
client = Client("sessions/LandSession", session_string=sessionString)

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