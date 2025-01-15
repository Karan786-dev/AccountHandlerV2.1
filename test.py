from pyrogram import Client
import asyncio


session_string = "BQAf70YAZtDQ7hfBYugYwQd3iwetDHLvulR4dkVNk9WyYWOHnHZEFBNdjvI3NLm7eME4alyf-6VR9rs6ouHBfzVUlkNIucn4L0a22hOoUvI-ZdJLHCCvC3tEMvzUB_ju7ZmSuzN_8eTNeGOBMPJ6Ql5h_y-sJ2XFN3i8NwSJ_Ya9vJZuJyS9s6ipY-647CXDNAhJEQFlmNAGIrH1BR3sCOdeS4xGaAKXB3X3S78JDU0eO_7v1naboGAHhLHM0pcBAHBsl7B9d419CQGEqgetnZghkNXGhbjNHphBQB7D5_S0rVH2Ju8kK1C_wjSvMFyyJAQztsYBHaQNjvSwPF-gCher_QAAAABXhc0CAA"

client = Client(name="MySession",session_string=session_string)


async def main():
    await client.connect()
    print(await client.send_message("me","Hello Karan"))
    await client.disconnect()

asyncio.run(main())