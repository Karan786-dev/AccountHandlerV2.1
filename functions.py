import time
import asyncio
import pytz
from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
import random
from datetime import datetime
from config import * 
import requests

timezone = pytz.timezone("Asia/Kolkata") 


class temp(object):
    ME = None
    CANCEL = False
    CURRENT = 0
    
    
def is_number(value):
    if isinstance(value, (int, float)):return True
    if isinstance(value, str):
        try:
            float(value) 
            return True
        except ValueError:return False
    return False




def convertTime(timestamp):
    if isinstance(timestamp, datetime): utc_time = timestamp
    else: utc_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    utc_time = pytz.utc.localize(utc_time)
    local_time = utc_time.astimezone(timezone)
    readable_format = local_time.strftime("%Y-%m-%d %I:%M:%S %p")
    return readable_format


def paginateArray(arr,page_size=2): return [arr[i:i + page_size] for i in range(0, len(arr), page_size)]

def shuffleArray(arr):
    shuffled = arr[:] 
    random.shuffle(shuffled) 
    return shuffled



def getProxies():
    with open("proxies.txt", "r") as file:
        proxies_file = file.readlines()
    proxies = []
    for proxy in proxies_file:
        proxy = proxy.strip()  # Remove any leading/trailing spaces or newlines
        if proxy:  # Skip empty lines
            parts = proxy.split(":")
            if len(parts) == 4:  # Ensure it has the expected structure
                host, port, username, password = parts
                proxies.append({
                    "host": host,
                    "port": int(port),
                    "username": username,
                    "password": password
                })
    return proxies



async def joinIfNot(client:Client,chatID,inviteLink):
    try:
        chatMember = await client.get_chat_member(chatID, "me")
        if not chatMember.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER , ChatMemberStatus.MEMBER]:
            channelData = await client.join_chat(inviteLink)
            print(f"Joined {chatID}")
            return channelData
        return await client.get_chat(chatID)
    except Exception as e:
        print("Error in joinIfNot",e)
        return False
    
async def logChannel(string):
    print(string)
    if not LOGGING_CHANNEL:return 
    try: return requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",{"chat_id": LOGGING_CHANNEL,"text": string})
    except Exception as e: print(string)