from functions import *
from database import *
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def changeValidity():
    allChannels = list(Channels.find({}))
    for channelData in allChannels:
        validity = channelData.get("validity",False)
        daysLeft = channelData.get("daysLeft",0)
        channelID = channelData.get("channelID")
        if not validity or not daysLeft: continue 
        updatedDocument = Channels.find_one_and_update({"channelID":int(channelID)},{"$inc":{"daysLeft":-1}},return_document=True)
        if not updatedDocument.get("daysLeft"):
            keyboard = {
                "inline_keyboard": [
                    [{"text": "➕ Add 30 Days","callback_data": f"/quickAddDays {channelID}:30"}]
                ]
            }
            logger.error(f"<b>[{channelData.get("title")}]</b>: Validity Expired\n\nAdd Days to continue serving.",keyboard=keyboard,printLog=False)
            

schedular = AsyncIOScheduler()

schedular.add_job(changeValidity,"cron",hour=0,minute=0)

async def main():
    print("Changing Validity Days")
    schedular.start()
    await asyncio.Event().wait()

if __name__ == "__main__": asyncio.run(main())