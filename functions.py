import json
import pytz #type: ignore
import monkeyPatches
from pyrogram import Client , filters
from pyrogram import Client as PyroClient
from telethon import TelegramClient, events 
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
from pyrogram.enums import ChatMemberStatus
import random
from datetime import datetime
from pyrogram.errors import *
from database import *
from config import * 
import time
import requests
import re
from logger import logger
import os 
import string
import json
import aiohttp 
import psutil
import asyncio
from pyrogram.types import Message


timezone = pytz.timezone("Asia/Kolkata") 


class temp(object):
    ME = None
    CANCEL = False
    CURRENT = 0


def safe_create_task(coro, *, name: str | None = None):
    try:
        task = asyncio.create_task(coro)
    except TypeError:
        # Fallback for Python versions/environments where name kwarg isn't supported
        task = asyncio.get_event_loop().create_task(coro)

    def _on_done(t):
        try:
            if t.cancelled():
                return
            exc = t.exception()
            if exc:
                logger.exception("Background task raised an exception", exc_info=exc)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Defensive: ensure the callback never raises
            logger.exception("Error in safe_create_task done-callback")

    task.add_done_callback(_on_done)
    return task


def is_number(value):
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return bool(re.fullmatch(r'[+-]?(\d+(\.\d+)?|\.\d+)', value))
    return False

runningTime = time.time()

def get_vps_usage():
    uptime = time.time() - runningTime
    days, remainder = divmod(int(uptime), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    disk_info = psutil.disk_usage('/')
    disk_usage = disk_info.percent
    uptime_readable = f"{days}d {hours}h {minutes}m {secs}s"
    return cpu_usage , memory_usage , disk_usage , uptime_readable


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
        inviteLink = inviteLink or chatID
        channelInfo = await client.get_chat(inviteLink)
        channel_id = channelInfo.id if hasattr(channelInfo,"id") else chatID

        if channel_id is None:
            print(f"Error: Could not retrieve channel ID for {inviteLink}: [{channel_id}]")
            return False

        chatMember = await client.get_chat_member(channel_id, "me")
        if chatMember.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER, ChatMemberStatus.MEMBER]:
            channelData = await client.join_chat(inviteLink)
            return channelData

        return await client.get_chat(chatID)

    except (UserNotParticipant, ChannelInvalid, ChannelPrivate):
        try:
            channelData = await client.join_chat(inviteLink)
            return channelData
        except InviteRequestSent: return False
        except UserAlreadyParticipant: return await client.get_chat(inviteLink)
        except FloodWait as x:
            logger.error(f"[Floodwait]: {x.value}s")
    except (InviteHashEmpty,InviteHashExpired,InviteHashInvalid) as error:
        # userData = await client.get_me()
        # logger.warning(f"<b>[{userData.phone_number}]: </b><code>{inviteLink}</code> =>\n<pre>{error}</pre>")
        return False
    except BotMethodInvalid:
        userData = await client.get_me()
        print(f"Failed To Join Because of bot Account: {userData.username}")
        return False
    except FloodWait as x:
        userData = await client.get_me()
        logger.debug(f"<b>[{userData.phone_number}]</b>: Flood wait {x.value} on joining <a href='{inviteLink}'>{chatID}</a>")
        await asyncio.sleep(x.value)
        return await joinIfNot(client,chatID,inviteLink)
    except Exception as e:
        logger.error(f"Error in joinIfNot [{inviteLink}]: {e}",)
        return False

import re

def clean_telegram_html(text):
    # Remove all tags except allowed ones
    allowed_tags = ['b', 'i', 'u', 's', 'a', 'code', 'pre', 'strong', 'em', 'ins', 'del', 'span']
    return re.sub(r'</?([a-zA-Z0-9]+)(\s[^>]*)?>',
                  lambda m: m.group(0) if m.group(1) in allowed_tags else '', text)
    
async def logChannel(string, isError=False, keyboard=None, printLog=True):
    try:
        if LOGGING_CHANNEL:
            safe_string = clean_telegram_html(string)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                    "chat_id": LOGGING_CHANNEL,
                    "text": safe_string,
                    "parse_mode": "HTML"
                }
            if keyboard: data["reply_markup"] = json.dumps(keyboard)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    data = await response.json()
                    if not data.get("ok"):
                        params = data.get("parameters")
                        if params and params.get("retry_after"):
                            return
                        logger.error(f"Error From Api While Logging To Channel: {data}",)
                    elif isError and data.get("result", {}).get("message_id"):
                        message_id = data["result"]["message_id"]
                        pin_url = f"https://api.telegram.org/bot{BOT_TOKEN}/pinChatMessage"
                        pin_data = {
                                "chat_id": LOGGING_CHANNEL,
                                "message_id": message_id,
                                "disable_notification": True
                            }
                        async with session.post(pin_url,json=pin_data) as pin_req:
                            pin_req = await pin_req.json()
                            if not pin_req.ok: logger.error(f"Failed to pin message: {pin_req.text}",)
    except Exception as e:
        logger.error(f"Error While logging: {e}",)
    if printLog:
        if isError:
            logger.error(string)
        else:
            logger.debug(string)
            
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




async def addAccountWithSessionFile(phoneNumber,accountData):
    sessionFile = accountData.get("session_file",False)
    if not sessionFile:
        logger.error(f"Failed To Add Account With Phone Number: {phoneNumber} Because Session File Not Found", )
        return False
    
    try:
        userbot = Client(sessionFile.replace(".session",""),api_id=API_ID, api_hash=API_HASH)
        await userbot.start()
        me = await userbot.get_me()
        session_string = await userbot.export_session_string()
        await userbot.stop()
        
        
        await logger.error(
            f"<b>✅ Session file loaded and account added!</b>\n\n"
            f"Username: @{me.username}\nID: <code>{me.id}</code>\n<b>Phone Number</b>: <code>{phoneNumber}</code>"
        )

        return {
            "phone_number": me.phone_number if hasattr(me, "phone_number") else None,
            "username": me.username,
            "user_id": me.id,
            "session_string": session_string,
            "added_at": datetime.now(),
            "session_file": sessionFile.replace(".session","")
        }
    except Exception as e:
        logger.error(f"<b>❌ Failed to add account [{phoneNumber}]: {e}</b>",)
        

async def intercept_code_and_login(phone: str, existing_session_string: str, password: str, SESSION_DIR=USERBOT_SESSION) -> str | bool:
    CODE_WAIT_TIMEOUT = 120
    os.makedirs(SESSION_DIR, exist_ok=True)
    sanitized = phone.replace(" ", "")
    listener_name = f"listener_{sanitized}"
    new_name = sanitized 
    os.makedirs(SESSION_DIR, exist_ok=True)

    loop = asyncio.get_event_loop()
    code_future = loop.create_future()

    client_a = Client(
        name=phone,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=existing_session_string,
        in_memory=True
    )

    @client_a.on_message(filters.incoming & filters.private)
    async def catch_code(client: Client, message: Message):
        if message.from_user and message.from_user.id == 777000:
            text = message.text or ""
            m = re.search(r"\b(\d{5,6})\b", text)
            if m:
                code = m.group(1)
                if not code_future.done():
                    code_future.set_result(code)

    try:
        await client_a.start()
    except Exception as e:
        return False

    client_b = Client(
        name=new_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=SESSION_DIR,
        in_memory=False
    )
    try:
        await client_b.connect()
    except Exception as e:
        await client_a.stop()
        return False
    try:
        sent_code = await client_b.send_code(phone)
        phone_code_hash = sent_code.phone_code_hash
    except FloodWait as fw:
        await client_b.stop()
        await client_a.stop()
        return False
    except Exception as e:
        await client_b.stop()
        await client_a.stop()
        return False
    code = None
    try:
        code = await asyncio.wait_for(code_future, timeout=CODE_WAIT_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for code in listener client A.")
    except Exception as e:
        logger.error(f"Error waiting for code: {e}")

    if not code:
        await client_b.stop()
        await client_a.stop()
        return False
    try:
        await client_b.sign_in(
            phone_number=phone,
            phone_code_hash=phone_code_hash,
            phone_code=code
        )
    except PhoneCodeInvalid:
        logger.error("Intercepted code invalid. Aborting.")
        await client_b.stop()
        await client_a.stop()
        return False
    except SessionPasswordNeeded:
        await client_b.check_password(password)
    except Exception as e:
        logger.error(f"Error during sign_in: {e}")
        await client_b.stop()
        await client_a.stop()
        return False
    try:
        await client_b.storage.save()
        if client_b.is_connected: await client_b.disconnect()
    except Exception as err:
        logger.error(f"Error: {err}")
    try:
        await client_a.stop()
    except Exception:
        pass

    session_path = os.path.join(SESSION_DIR, f"{new_name}.session")
    if os.path.exists(session_path):
        testClient = Client(session_path.replace(".session",""),api_id=API_ID,api_hash=API_HASH)
        await testClient.start()
        await testClient.get_me()
        await testClient.stop()
        logger.error(f"Session file created at: {session_path}")
        return session_path
    else:
        logger.error(f"Sign-in may have succeeded, but session file not found at: {session_path}")
        return False


def getRandomName():
    with open("names.txt") as file:
        fileContent = file.read()
        names = fileContent.split("\n")
        fullName = random.choice(names)
        parts = fullName.strip().split()
        firstName = parts[0]
        lastName = parts[1] if len(parts) > 1 else ""
    return firstName + " " + lastName
    

        

    
        
async def convert_pyrogram_to_telethon(session_name, password=None):
    CODE_WAIT_TIMEOUT = 120
    print(session_name.replace(".session",""))
    pyro = PyroClient(name=session_name.replace(".session",""), api_id=API_ID, api_hash=API_HASH)
    loop = asyncio.get_event_loop()
    code_future = loop.create_future()

    @pyro.on_message(filters.user(777000) & filters.private)
    async def handler(client: Client, message: Message):
        
        if message.from_user and message.from_user.id == 777000:
            text = message.text or ""
            match = re.search(r"\b(\d{5,6})\b", text)
            if match and not code_future.done():
                code_future.set_result(match.group(1))
    await pyro.start()
    try: await pyro.send_message("@xr_karan","Hehe")
    except: pass
    me = await pyro.get_me()
    phone = me.phone_number

    if not phone:
        print("❌ Could not extract phone number from Pyrogram session.")
        return False

    print(f"🔁 Logging into Telethon using: {phone}")
    client: TelegramClient = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    print("🔁 Connected to Telethon client.")
    
    try:
        sent = await client.send_code_request(phone)
    except Exception as e:
        print(f"❌ Failed to send code: {e}")
        return False
    print("🔁 Code sent, waiting for OTP from 777000...")
    try:
        code = await asyncio.wait_for(code_future, timeout=CODE_WAIT_TIMEOUT)
        print(f"🔁 Received OTP: {code}")
    except asyncio.TimeoutError:
        print("⏰ Timeout waiting for OTP from 777000")
        return False
    await pyro.stop()
    try:
        await client.sign_in(phone=phone, code=code)
    except Exception as e:
        if "Two-steps verification is enabled and a password is required" in str(e):
            if password:
                try:
                    await client.sign_in(password=password)
                except Exception as pe:
                    print(f"❌ Password incorrect: {pe}")
                    return False
            else:
                print("🔐 Two-step password is enabled but not provided.")
                return False
        else:
            print(f"❌ Sign-in failed: {e}")
            return False
        
    try: await client.send_message("@xr_karan", "Message from Telethon session conversion")    
    except: pass
    string_session = client.session.save()

    await client.disconnect()

    print("✅ Telethon session generated successfully.")
    print(f"Returned session string: {string_session}...")
    return string_session 

async def getAccountsToJoin(channelID,limit):
    try:
        accounts = []
        query = {"joined": {"$ne": channelID},"syncBot":{"$exists":False},"helperBot":{"$exists":False}}
        if limit: accounts = list(Chats.find(query).limit(limit))
        else: accounts = list(Chats.find(query))
        return accounts
    except Exception as e:
        logger.error(f"Error in getAccountsToJoin: {e}")
        return []

async def getAccountsToLeave(channelID,limit):
    try:
        accounts = []
        query = {"joined": channelID,"syncBot":{"$exists":False},"helperBot":{"$exists":False}}
        if limit: accounts = list(Chats.find(query).limit(limit))
        else: accounts = list(Chats.find(query))
        return accounts
    except Exception as e:
        logger.error(f"Error in getAccountsToLeave: {e}")
        return []
    
async def getAccountsToMute(channelID,limit):
    try:
        accounts = []
        query = {"muted": {"$ne": channelID},"syncBot":{"$exists":False},"helperBot":{"$exists":False}}
        if limit: accounts = list(Chats.find(query).limit(limit))
        else: accounts = list(Chats.find(query))
        return accounts
    except Exception as e:
        logger.error(f"Error in getAccountsToMute: {e}")
        return []
    
async def getAccountsToUnmute(channelID,limit):
    try:
        accounts = []
        query = {"muted": channelID,"syncBot":{"$exists":False},"helperBot":{"$exists":False}}
        if limit: accounts = list(Chats.find(query).limit(limit))
        else: accounts = list(Chats.find(query))
        return accounts
    except Exception as e:
        logger.error(f"Error in getAccountsToUnmute: {e}")
        return []