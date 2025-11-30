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


async def doActivity(channelID):
    log_activity(channelID,"Channel Activity Started")
    activityData = ActivityChannels.find_one({"channelID": int(channelID)})
    minJoin = activityData.get("minimumJoin", 0)
    maxJoin = activityData.get("maximumJoin", 0)
    channelLink = activityData.get("inviteLink", None)
    channelTitle = activityData.get("title", None)
    channelID = activityData.get("channelID")
    minLeave = activityData.get("minimumLeave", 0)
    maxLeave = activityData.get("maximumLeave", 0)
    minMute = activityData.get("minimumMute", 0)
    maxMute = activityData.get("maximumMute", 0)
    minUnmute = activityData.get("minimumUnmute", 0)
    maxUnmute = activityData.get("maximumUnmute", 0)
    
    joinCount = random.randint(minJoin, maxJoin)
    leaveCount = random.randint(minLeave, maxLeave)
    muteCount = random.randint(minMute,maxMute)
    unmuteCount = random.randint(minUnmute,maxUnmute)

    # Process operations concurrently but with proper error handling
    try:
        # Start join operation
        accountsToJoin = await getAccountsToJoin(channelID,joinCount)
        randomJoinDelay = random_delays(len(accountsToJoin))
        log_activity(channelID,f"Joining {len(accountsToJoin)} accounts to {channelTitle}: Delays: {randomJoinDelay}")
        join_task = UserbotManager.bulk_order(accountsToJoin, {
            "type": "join_channel",
            "channels":[channelLink],
            "restTime":randomJoinDelay,
            "taskPerformCount":joinCount
        })

        # Start name changes
        name_tasks = []
        for i in accountsToJoin:
            newName = getRandomName()
            while Accounts.find_one({"name":newName}): newName = getRandomName()
            name_task = UserbotManager.add_task(
                i.get('phone_number'),
                {
                    "type": "changeName",
                    "firstName": newName.split(" ")[0],
                    "lastName": newName.split(" ")[1]
                }
            )
            name_tasks.append(name_task)
            Accounts.update_one({"phone_number":i.get("phone_number")},{"$set":{"name":newName}})

        # Start leave operation
        accountsToLeave = await getAccountsToLeave(channelID,leaveCount)
        randomLeaveDelay = random_delays(len(accountsToLeave))
        log_activity(channelID,f"Leaving {len(accountsToLeave)} accounts from {channelTitle}: Delays: {randomLeaveDelay}")
        leave_task = UserbotManager.bulk_order(accountsToLeave, {
            "type": "leave_channel",
            "channels":[channelID],
            "restTime":randomLeaveDelay,
            "taskPerformCount":leaveCount
        })

        # Start mute operation
        accountsToMute = await getAccountsToMute(channelID,muteCount)
        randomMuteDelay = random_delays(len(accountsToMute))
        log_activity(channelID,f"Muting {len(accountsToMute)} accounts in {channelTitle}: Delays: {randomMuteDelay}: Accounts List- {[i.get('phone_number') for i in accountsToMute]}")
        mute_task = UserbotManager.bulk_order(accountsToMute, {
            "type":"changeNotifyChannel",
            "chatID":channelID,
            "restTime":randomMuteDelay,
            "taskPerformCount": muteCount,
            "inviteLink":channelLink,
            "duration": 2147483647
        })

        # Start unmute operation
        accountsToUnmute = await getAccountsToUnmute(channelID,unmuteCount)
        randomUnmuteDelay = random_delays(len(accountsToUnmute))
        log_activity(channelID,f"Unmuting {len(accountsToUnmute)} accounts in {channelTitle}: Delays: {randomUnmuteDelay} ")
        unmute_task = UserbotManager.bulk_order(accountsToUnmute,{
            "type":"changeNotifyChannel",
            "chatID":channelID,
            "restTime":randomUnmuteDelay,
            "taskPerformCount": unmuteCount,
            "inviteLink":channelLink,
            "duration": 0
        })

        # Run all operations concurrently and wait for completion
        tasks = [join_task]
        tasks.extend(name_tasks)
        tasks.extend([leave_task, mute_task, unmute_task])
        
        # Filter out None tasks (in case some operations had no accounts to process)
        tasks = [t for t in tasks if t is not None]
        
        if tasks:
            await asyncio.gather(*tasks)
            
    except Exception as e:
        log_activity(channelID, f"Error in channel activity: {str(e)}")
        await logChannel(f"❌ Error in channel {channelTitle} ({channelID}): {str(e)}")

    

def random_delays(num_accounts, total_minutes=20*60, spread=0.5):
    if num_accounts < 1: return [0,0]

    avg_delay = total_minutes / num_accounts
    min_delay = avg_delay * (1 - spread)
    max_delay = avg_delay * (1 + spread)
    # return [0,0]
    return [min_delay*60, max_delay*60]

MAX_CONCURRENT_CHANNELS = 5  # Adjust this value based on your needs
channel_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHANNELS)

async def process_channel(channel):
    async with channel_semaphore:
        channelID = channel.get("channelID")
        await doActivity(channelID)

async def startRandomActivityInChannels():
    channels = list(ActivityChannels.find({}))
    await logChannel(f"<b>🔄 Running Random Activity in Channels.</b>\n\n<b>Total Channels</b>: <code>{len(channels)}</code>")
    
    # Create tasks for all channels but limit concurrent execution
    tasks = [asyncio.create_task(process_channel(channel)) for channel in channels]
    
    # Wait for all channels to complete while allowing concurrent processing
    await asyncio.gather(*tasks)

async def main():
    while True:
        await doActivity(-1003060090488)
        await asyncio.sleep(5*60)
        break


# if __name__ == "__main__":
#     asyncio.run(main())