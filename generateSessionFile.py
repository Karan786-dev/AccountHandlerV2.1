import asyncio
import re
import os
from pyrogram import Client, filters
from database import Accounts
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, FloodWait
from pyrogram.types import Message
from config import API_ID, API_HASH, USERBOT_SESSION

MAX_CONCURRENT = 20
CODE_WAIT_TIMEOUT = 120
SESSION_DIR = USERBOT_SESSION
os.makedirs(SESSION_DIR, exist_ok=True)

async def intercept_code_and_login(phone: str, existing_session_string: str, password: str | None) -> dict:
    result = {
        "phone": phone,
        "success": False,
        "session_path": None,
        "new_session_string": None,
        "error": None
    }
    sanitized = phone.replace("+", "").replace(" ", "")
    listener_name = f"listener_{sanitized}"
    new_name = sanitized
    os.makedirs(SESSION_DIR, exist_ok=True)
    loop = asyncio.get_event_loop()
    code_future = loop.create_future()
    client_a = Client(
        name=listener_name,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=existing_session_string,
        workdir=SESSION_DIR,
        in_memory=False,
    )
    @client_a.on_message(filters.incoming & filters.private)
    async def catch_code(client: Client, message: Message):
        if message.from_user and message.from_user.id == 777000:
            text = message.text or ""
            m = re.search(r"\b(\d{5,6})\b", text)
            if m and not code_future.done():
                code_future.set_result(m.group(1))
                print(f"[{phone}] Intercepted code: {m.group(1)}")
    try:
        await client_a.start()
    except Exception as e:
        result["error"] = f"Failed to start listener: {e}"
        return result
    client_b = Client(
        name=new_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=SESSION_DIR,
        in_memory=False,
    )
    try:
        await client_b.connect()
    except Exception as e:
        result["error"] = f"Failed to start client B: {e}"
        await client_a.stop()
        return result
    try:
        sent_code = await client_b.send_code(phone)
        phone_code_hash = sent_code.phone_code_hash
        print(f"[{phone}] Requested login code, phone_code_hash: {phone_code_hash}")
    except FloodWait as fw:
        result["error"] = f"FloodWait: {fw.x}s"
        await client_b.disconnect()
        await client_a.stop()
        return result
    except Exception as e:
        result["error"] = f"Failed to send code request: {e}"
        await client_b.disconnect()
        await client_a.stop()
        return result
    code = None
    try:
        code = await asyncio.wait_for(code_future, timeout=CODE_WAIT_TIMEOUT)
        print(f"[{phone}] Code received: {code}")
    except asyncio.TimeoutError:
        result["error"] = "Timeout waiting for code"
    except Exception as e:
        result["error"] = f"Error waiting for code: {e}"
    if not code:
        await client_b.disconnect()
        await client_a.stop()
        return result
    try:
        await client_b.sign_in(
            phone_number=phone,
            phone_code_hash=phone_code_hash,
            phone_code=code
        )
    except PhoneCodeInvalid:
        result["error"] = "Invalid code"
        await client_b.disconnect()
        await client_a.stop()
        return result
    except SessionPasswordNeeded:
        if password:
            try:
                await client_b.check_password(password)
            except Exception as e:
                result["error"] = f"2FA check failed: {e}"
                await client_b.disconnect()
                await client_a.stop()
                return result
        else:
            result["error"] = "2FA enabled, no password"
            await client_b.disconnect()
            await client_a.stop()
            return result
    except Exception as e:
        result["error"] = f"Error during sign_in: {e}"
        await client_b.disconnect()
        await client_a.stop()
        return result
    try:
        new_str = await client_b.export_session_string()
        result["new_session_string"] = new_str
    except Exception:
        pass
    try:
        await client_b.disconnect()
    except:
        pass
    try:
        await client_a.stop()
    except:
        pass
    session_path = os.path.join(SESSION_DIR, f"{new_name}.session")
    if os.path.exists(session_path):
        result["success"] = True
        result["session_path"] = session_path
    else:
        result["error"] = result.get("error") or "Session file not found"
    return result

async def main():
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    accounts = list(Accounts.find({}))
    if not accounts:
        print("No accounts found")
        return
    print(f"Found {len(accounts)} accounts, running up to {MAX_CONCURRENT} in parallel")
    async def worker(account_doc):
        phone = account_doc.get("phone_number")
        sess_str = account_doc.get("session_string")
        password = account_doc.get("password", None)
        if not phone or not sess_str:
            return {
                "phone": phone or "<missing>",
                "success": False,
                "session_path": None,
                "new_session_string": None,
                "error": "Missing phone or session_string"
            }
        async with sem:
            print(f"[{phone}] Starting refresh")
            res = await intercept_code_and_login(phone, sess_str, password)
            print(f"[{phone}] Done: {'Success' if res.get('success') else 'Failure'}, error={res.get('error')}")
            return res
    tasks = [asyncio.create_task(worker(doc)) for doc in accounts]
    all_results = await asyncio.gather(*tasks)
    summary = {"success": [], "failed": []}
    for res in all_results:
        phone = res.get("phone")
        if res.get("success"):
            summary["success"].append(phone)
            update_fields = {"session_file": res["session_path"]}
            if res.get("new_session_string"):
                update_fields["session_string"] = res["new_session_string"]
            try:
                Accounts.update_one(
                    {"phone_number": phone},
                    {"$set": update_fields}
                )
                print(f"[{phone}] DB updated")
            except Exception as e:
                print(f"[{phone}] DB update failed: {e}")
        else:
            summary["failed"].append((phone, res.get("error")))
    print("Summary:")
    print("  Success:", len(summary["success"]), summary["success"])
    print("  Failed:", len(summary["failed"]), summary["failed"])

if __name__ == "__main__":
    asyncio.run(main())
