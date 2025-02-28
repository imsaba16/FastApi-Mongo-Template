from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "pymongo"

client = AsyncIOMotorClient(
    MONGO_URI,
    maxPoolSize=100,
    minPoolSize=10
)
database = client[DB_NAME]
user_collection = database["user"]
