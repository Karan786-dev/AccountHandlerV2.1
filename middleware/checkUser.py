from database import Users


async def checkUser(_, msg):
    userID = msg.from_user.id
    userData = Users.find_one({"userID": userID})
    if not userData:
        userData = {"userID": userID}
        Users.insert_one(userData)
    if userData.get('is_banned'):
        await msg.reply("<b>You are banned from this bot</b>")
        return False
    return True
