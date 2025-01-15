from config import ADMINS


def authAdmin(_, msg):
    if not (msg.from_user.id in ADMINS):
        return False
    return True