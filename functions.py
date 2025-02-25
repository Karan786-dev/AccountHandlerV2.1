import json
import pytz #type: ignore
from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
import random
from datetime import datetime
from pyrogram.errors import *
from config import * 
import requests
import re
from logger import logger
import string
import json

timezone = pytz.timezone("Asia/Kolkata") 


class temp(object):
    ME = None
    CANCEL = False
    CURRENT = 0


def is_number(value):
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return bool(re.fullmatch(r'[+-]?(\d+(\.\d+)?|\.\d+)', value))
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

def checkProxy(ip,port,username,password):
    proxy = f"http://{username}:{password}@{ip}:{port}"
    proxies = {
        "http": proxy,
        "https": proxy
    }
    try:
        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
        if response.status_code == 200: return True
        else:
            print("Proxy responded with status:", response.status_code)
            return False
    except requests.exceptions.RequestException as e:
        print("Proxy failed:", e)
        return False

async def joinIfNot(client: Client, chatID, inviteLink):
    try:
        if not inviteLink: return False
        channelInfo = await client.get_chat(inviteLink)
        channel_id = getattr(channelInfo, "id", None)

        if channel_id is None:
            print(f"Error: Could not retrieve channel ID for {inviteLink}")
            return False

        chatMember = await client.get_chat_member(channel_id, "me")
        if chatMember.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER, ChatMemberStatus.MEMBER]:
            channelData = await client.join_chat(inviteLink)
            print(f"Joined {chatID}")
            return channelData

        return await client.get_chat(chatID)

    except (UserNotParticipant, ChannelInvalid, ChannelPrivate):
        channelData = await client.join_chat(inviteLink)
        print(f"Joined {chatID}")
        return channelData

    except BotMethodInvalid:
        userData = await client.get_me()
        print(f"Failed To Join Because of bot Account: {userData.username}")

    except Exception as e:
        print(f"Error in joinIfNot: {e}")
        return False

    
def logChannel(string,isError=False,keyboard=None):
    try: 
        if LOGGING_CHANNEL: 
            request = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                    {"chat_id": LOGGING_CHANNEL,
                                     "text": string,
                                     "parse_mode":"HTML",
                                     "reply_markup":json.dumps(keyboard) if keyboard else keyboard
                                    })
            data = request.json()
            if not data.get("ok"): logger.error(f"Error From Api While Logging To Channel: {data}")
    except Exception as e: logger.error(f"Error While logChannel: {e}")
    if isError: logger.error(string)
    else: logger.debug(string)

def format_json(json_string):
    try:
        if not isinstance(json_string, str):
            json_string = json.dumps(json_string) 
        json_string = json_string.replace("'", '"')
        data = json.loads(json_string)
        for key, value in data.items():
            if isinstance(value, bool): data[key] = str(value) 
        return "\n".join(f"<b>{key}:</b>  <code>{value}</code>" for key, value in data.items())
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        return json_string 


def generateRandomString(length=5):
    characters = string.ascii_letters
    return ''.join(random.choice(characters) for _ in range(length))