from config import ADMINS


def authAdmin(_, msg): return msg.from_user.id in ADMINS