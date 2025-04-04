from database import *
from functions import *
from orderAccounts import *
from config import *
from pyrogram import Client, types
import asyncio 
import random
import os
import faker

os.makedirs(ACTIVITY_DATA_FOLDER, exist_ok=True)

async def leaveChannelAfterDelay(phoneNumber,channelID,channelLink,Delay,taskFile):
    await asyncio.sleep(Delay)
    await UserbotManager.add_task(
        phoneNumber,
        {
            "type":"leave_channel",
            "channels":[channelID],
        }
    )
    os.remove(taskFile)
    
    
async def doActivity(channelID):
    while True:   
        channelData = ActivityChannels.find_one({"channelID":int(channelID)})
        if not channelData: return None 
        activityStatus = channelData.get("activityStatus",False)
        if not activityStatus: break
        channelLink = channelData.get("inviteLink",None)
        maxJoinDelay = channelData.get("maxJoinDelay",0)
        minJoinDelay = channelData.get("minJoinDelay",0)
        maxLeaveDelay = channelData.get("maxLeaveDelay",0)
        minLeaveDelay = channelData.get("minLeaveDelay",0)
        muteProbability = channelData.get("muteProbability",0)
        random_joinDelay = random.randint(minJoinDelay,maxJoinDelay)
        random_leaveDelay = random.randint(minLeaveDelay,maxLeaveDelay)
        shouldMute = random.randint(1,100) <= muteProbability
        randomUserbot = Accounts.aggregate([{'$sample': {'size': 1}}]).next()
        phoneNumber = randomUserbot.get("phone_number")
        
        await asyncio.sleep(random_joinDelay)
        await UserbotManager.add_task(
            phoneNumber,
            {
                "type": "changeName",
                "firstName": faker.Faker("en_IN").first_name(),
            }
        )
        await UserbotManager.add_task(
            phoneNumber,
            {
                "type":"join_channel",
                "channels":[channelLink or channelID],
            }
        )
        
        if shouldMute:
            await UserbotManager.add_task(
                phoneNumber,
                {
                    "type":"changeNotifyChannel",
                    "chatID": channelID,
                    "inviteLink":channelLink,
                    "duration": random.randint(minLeaveDelay,random_leaveDelay),
                }
            )
        
        dataFile = f"{ACTIVITY_DATA_FOLDER}/{generateRandomString(10)}.json"
        
        with open(dataFile,"w") as f:
            json.dump({"channelID":channelID,"phoneNumber":phoneNumber,"delay":random_leaveDelay,"channelLink":channelLink},f)
        
        asyncio.create_task(
            leaveChannelAfterDelay(
                phoneNumber,
                channelID,
                channelLink,
                random_leaveDelay,
                dataFile
            )
        )
            
        
async def startRandomActivityInChannels():
    channels = list(ActivityChannels.find({}))
    for i in channels:
        channelID  = i.get("channelID")
        asyncio.create_task(doActivity(channelID)) 
        
async def restart_pendingLeaves():
    pendingLeaves = os.listdir(ACTIVITY_DATA_FOLDER)
    for i in pendingLeaves:
        file = f"{ACTIVITY_DATA_FOLDER}/{i}"
        with open(file,"r") as f:
            data = json.load(f)
            channelID = data.get("channelID")
            phoneNumber = data.get("phoneNumber")
            Delay = data.get("delay")
            channelLink = data.get("channelLink")
            asyncio.create_task(
                leaveChannelAfterDelay(
                    phoneNumber,
                    channelID,
                    channelLink,
                    Delay,
                    file
                )
            )
        