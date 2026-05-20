from fastapi import FastAPI, HTTPException, Path
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

# ---------------- DB SETUP ----------------
client = AsyncIOMotorClient(MONGODB_URI)

db = client["ai-todo-app"]   # database name
todo_collection = db["todos"]

# ---------------- APP ----------------
app = FastAPI()

# ---------------- MODELS ----------------
class TodoCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    checked: bool = False


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    checked: Optional[bool] = None


# ---------------- HELPER ----------------
def todo_helper(todo) -> dict:
    return {
        "id": str(todo["_id"]),
        "title": todo.get("title"),
        "description": todo.get("description"),
        "checked": todo.get("checked", False),
        "createdAt": todo.get("createdAt"),
        "updatedAt": todo.get("updatedAt"),
    }


def validate_object_id(todo_id: str) -> ObjectId:
    try:
        return ObjectId(todo_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")


# ---------------- ROUTES ----------------

@app.get("/todos")
async def get_todos():
    todos = await todo_collection.find().to_list(length=None)

    return {
        "success": True,
        "count": len(todos),
        "data": [todo_helper(todo) for todo in todos]
    }


@app.get("/todos/{todo_id}")
async def get_todo(todo_id: str = Path(...)):
    obj_id = validate_object_id(todo_id)

    todo = await todo_collection.find_one({"_id": obj_id})

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"success": True, "data": todo_helper(todo)}


@app.post("/todos", status_code=201)
async def create_todo(todo: TodoCreate):
    now = datetime.now(timezone.utc)

    todo_data = todo.model_dump()
    todo_data["createdAt"] = now
    todo_data["updatedAt"] = now

    result = await todo_collection.insert_one(todo_data)

    created = await todo_collection.find_one({"_id": result.inserted_id})

    return {
        "success": True,
        "message": "Todo created",
        "data": todo_helper(created)
    }


@app.patch("/todos/{todo_id}")
async def update_todo(
    todo_id: str = Path(...),
    todo: TodoUpdate = None
):
    obj_id = validate_object_id(todo_id)

    update_data = todo.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    update_data["updatedAt"] = datetime.now(timezone.utc)

    result = await todo_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found")

    updated = await todo_collection.find_one({"_id": obj_id})

    return {
        "success": True,
        "message": "Updated successfully",
        "data": todo_helper(updated)
    }


@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str = Path(...)):
    obj_id = validate_object_id(todo_id)

    result = await todo_collection.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {
        "success": True,
        "message": "Deleted successfully"
    }
