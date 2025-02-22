from app.database import users_collection
from app.core.security import hash_password, verify_password
from app.utils.token import create_access_token
from app.schemas import UserCreate, UserDB
from bson import ObjectId

async def create_user(user: UserCreate):
    existing_user = await users_collection.find_one({
        "$or": [{"email": user.email}, {"username": user.username}]
    })
    if existing_user:
        return None 

    hashed_pw = hash_password(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_pw,
    }
    
    result = await users_collection.insert_one(new_user)
    return UserDB(id=str(result.inserted_id), **new_user)

async def authenticate_user(identifier: str, password: str):
    user = await users_collection.find_one({
        "$or": [{"email": identifier}, {"username": identifier}]
    })

    if not user or not verify_password(password, user["hashed_password"]):
        return None

    return UserDB(id=str(user["_id"]), **user)

async def get_user_by_id(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return UserDB(id=str(user["_id"]), **user)
    return None
