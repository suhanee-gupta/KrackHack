from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "PixelForge"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]
users_collection = db["users"]
