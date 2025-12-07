import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URL")

try:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["SCM"]
    print("MongoDB Connected Successfully")
except Exception as e:
    print("❌ MongoDB Connection Error:", e)

users_collection = db["users"]
shipments = db["shipments"]
devices = db["devices"]
device_stream_collection = db["device_stream"]
