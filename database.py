from pymongo import MongoClient  # type: ignore
from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
from config import MONGO_URL , DB_NAME


try:
    client = MongoClient(MONGO_URL)
    mydb = client[DB_NAME]
    Admin = mydb['admin']
    Users = mydb['users']
    Accounts = mydb['accounts']
    Transactions = mydb["Transactions"]
    Channels = mydb["channels"]
    ActivityChannels = mydb["activity_channels"]
except Exception as e:
    print("Error connecting to MongoDB: ", e)
