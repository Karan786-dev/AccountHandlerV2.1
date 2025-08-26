from database import *
from functions import *
from orderAccounts import *
from config import *
from pyrogram import Client, types
import asyncio 
import random
import os
import json
import datetime

os.makedirs(ACTIVITY_DATA_FOLDER, exist_ok=True)
LOGS_FOLDER = "ActivityLogs"
os.makedirs(LOGS_FOLDER, exist_ok=True)

def log_activity(channelID, message):
    channelData = ActivityChannels.find_one({"channelID": int(channelID)})
    if not channelData: return
    logFile = os.path.join(LOGS_FOLDER, f"{channelData.get("title")}-log.txt")
    with open(logFile, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} - {message}\n")

async def unmuteAfterDelay(phoneNumber,channelID,channelLink,Delay,taskFile):
    channelData = ActivityChannels.find_one({"channelID": int(channelID)})
    if not channelData: 
      log_activity(channelID,f"[{channelID}] Channel Removed from Database. Deleting its pending task file.")
      return os.remove(taskFile)
    log_activity(channelID, f"[{phoneNumber}] Scheduled to unmute after {Delay}s.")
    await asyncio.sleep(Delay)
    await UserbotManager.add_task(
            phoneNumber,
            {
                "type": "changeNotifyChannel",
                "chatID": channelID,
                "duration": 0,
                "inviteLink": channelLink
            }
    )
    os.remove(taskFile)
    log_activity(channelID, f"[{phoneNumber}] Unmuted and removed task file: {taskFile}")

async def leaveChannelAfterDelay(phoneNumber, channelID, channelLink, Delay, taskFile):
    channelData = ActivityChannels.find_one({"channelID": int(channelID)})
    if not channelData: 
      log_activity(channelID,f"[{channelID}] Channel Removed from Database. Deleting its pending task file.")
      return os.remove(taskFile)
    log_activity(channelID, f"[{phoneNumber}] Scheduled to leave after {Delay}s.")
    await asyncio.sleep(Delay)
    await UserbotManager.add_task(
        phoneNumber,
        {
            "type": "leave_channel",
            "channels": [channelID],
        }
    )
    os.remove(taskFile)
    log_activity(channelID, f"[{phoneNumber}] Left and removed task file: {taskFile}")

async def doActivity(channelID):
    while True:   
        channelData = ActivityChannels.find_one({"channelID": int(channelID)})
        if not channelData:
            return None 
        activityStatus = channelData.get("activityStatus", False)
        if not activityStatus:
            break
        channelLink = channelData.get("inviteLink", None)
        maxJoinDelay = channelData.get("maxJoinDelay", 0)
        minJoinDelay = channelData.get("minJoinDelay", 0)
        maxLeaveDelay = channelData.get("maxLeaveDelay", 0)
        minLeaveDelay = channelData.get("minLeaveDelay", 0)
        muteProbability = channelData.get("muteProbability", 0)
        unmuteProbability = channelData.get("unmuteProbability", 0)

        if minJoinDelay > maxJoinDelay:
            minJoinDelay, maxJoinDelay = 0, 0
        if minLeaveDelay > maxLeaveDelay:
            minLeaveDelay, maxLeaveDelay = 0, 0

        random_joinDelay = random.randint(minJoinDelay, maxJoinDelay)
        random_leaveDelay = random.randint(minLeaveDelay, maxLeaveDelay)
        shouldMute = random.randint(1, 100) <= muteProbability
        shouldUnmute = random.randint(1,100) <= unmuteProbability
        unmuteDelay = random.randint(minLeaveDelay,random_leaveDelay)


        try:
            randomUserbot = Accounts.aggregate([{'$sample': {'size': 1}}]).next()
        except StopIteration:
            log_activity(channelID, "No userbots available.")
            return

        phoneNumber = randomUserbot.get("phone_number")
        
        isSyncBot = randomUserbot.get("syncBot")
        if isSyncBot: continue
        await asyncio.sleep(random_joinDelay)

        firstName = ""
        lastName = ""
        with open("names.txt") as file:
            fileContent = file.read()
            names = fileContent.split("\n")
            fullName = random.choice(names)
            parts = fullName.strip().split()
            firstName = parts[0]
            lastName = parts[1] if len(parts) > 1 else ""

        
        await UserbotManager.add_task(
            phoneNumber,
            {
                "type": "leave_channel",
                "channels": [channelLink or channelID]
            }
        )
        await asyncio.sleep(5)
        await UserbotManager.add_task(
            phoneNumber,
            {
                "type": "changeName",
                "firstName": firstName,
                "lastName": lastName
            }
        )
        log_activity(channelID, f"[{phoneNumber}] Changed name to: {firstName} {lastName}")
        
        await asyncio.sleep(10)

        await UserbotManager.add_task(
            phoneNumber,
            {
                "type": "join_channel",
                "channels": [channelLink or channelID],
            }
        )
        log_activity(channelID, f"[{phoneNumber}] Joined. Will leave after {random_leaveDelay}s. Muted: {shouldMute}")

        muteUntill = 2147483647 #Forever :)
        await UserbotManager.add_task(
            phoneNumber,
            {
                "type": "changeNotifyChannel",
                "chatID": channelID,
                "inviteLink": channelLink,
                "duration": muteUntill if shouldMute else 0,
            }
        )
        if shouldMute: log_activity(channelID, f"[{phoneNumber}] Muted notifications.")


        dataFile = f"{ACTIVITY_DATA_FOLDER}/{generateRandomString(10)}.json"
        with open(dataFile, "w") as f:
            json.dump({"type":"leave","channelID": channelID, "phoneNumber": phoneNumber, "delay": random_leaveDelay}, f)

        asyncio.create_task(
            leaveChannelAfterDelay(
                phoneNumber,
                channelID,
                channelLink,
                random_leaveDelay,
                dataFile,

            )
        )

        if shouldUnmute:
            dataFile = f"{ACTIVITY_DATA_FOLDER}/{generateRandomString(10)}.json"
            with open(dataFile, "w") as f:
                json.dump({"type":"unmute","channelID": channelID, "phoneNumber": phoneNumber, "delay": unmuteDelay}, f)
            asyncio.create_task(
                unmuteAfterDelay(
                    phoneNumber,
                    channelID,
                    channelLink,
                    unmuteDelay,
                    dataFile
                )
            )


async def startRandomActivityInChannels():
    channels = list(ActivityChannels.find({}))
    for i in channels:
        channelID = i.get("channelID")
        asyncio.create_task(doActivity(channelID)) 

async def restart_pendingLeaves():
    pendingLeaves = os.listdir(ACTIVITY_DATA_FOLDER)
    for i in pendingLeaves:
        file = f"{ACTIVITY_DATA_FOLDER}/{i}"
        try:
            with open(file, "r") as f:
                data = json.load(f)
                channelID = data.get("channelID")
                phoneNumber = data.get("phoneNumber")
                Delay = data.get("delay")
                channelLink = data.get("channelLink",None)
                taskType = data.get("type","leave")
                if taskType == "leave":
                    asyncio.create_task(
                        leaveChannelAfterDelay(
                            phoneNumber,
                            channelID,
                            channelLink,
                            Delay,
                            file
                        )
                    )
                elif taskType == "unmute":
                    asyncio.create_task(
                    unmuteAfterDelay(
                        phoneNumber,
                        channelID,
                        Delay,
                        file
                    )
        )
        except Exception as e:
            continue