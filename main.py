from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from db import todo_collection

app = FastAPI()


# 🔹 Todo Schema
class Todo(BaseModel):
    title: str
    description: Optional[str] = None
    checked: bool = False


# 🔹 Helper function
def todo_helper(todo) -> dict:
    return {
        "id": str(todo["_id"]),
        "title": todo["title"],
        "description": todo.get("description"),
        "checked": todo.get("checked", False),
        "createdAt": todo.get("createdAt"),
        "updatedAt": todo.get("updatedAt"),
    }


# 🟢 GET all todos
@app.get("/todos")
async def get_todos():
    try:
        todos = [todo_helper(todo) async for todo in todo_collection.find()]

        return {
            "success": True,
            "data": todos
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 🔵 GET single todo
@app.get("/todos/{todo_id}")
async def get_todo(todo_id: str):
    try:
        try:
            obj_id = ObjectId(todo_id)

        except InvalidId:
            raise HTTPException(
                status_code=400,
                detail="Invalid ID format"
            )

        todo = await todo_collection.find_one({"_id": obj_id})

        if not todo:
            raise HTTPException(
                status_code=404,
                detail="Todo not found"
            )

        return {
            "success": True,
            "data": todo_helper(todo)
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 🟣 POST create todo
@app.post("/todos", status_code=201)
async def create_todo(todo: Todo):
    try:
        if not todo.title.strip():
            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty"
            )

        raw_data = {
            k: v
            for k, v in todo.dict().items()
            if v is not None
        }

        now = datetime.now(timezone.utc).isoformat()

        raw_data["createdAt"] = now
        raw_data["updatedAt"] = now

        result = await todo_collection.insert_one(raw_data)

        new_todo = await todo_collection.find_one(
            {"_id": result.inserted_id}
        )

        return {
            "success": True,
            "data": todo_helper(new_todo)
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 🟡 PATCH update todo
@app.patch("/todos/{todo_id}")
async def update_todo(todo_id: str, updated_todo: Todo):
    try:
        try:
            obj_id = ObjectId(todo_id)

        except InvalidId:
            raise HTTPException(
                status_code=400,
                detail="Invalid ID format"
            )

        update_data = {
            k: v
            for k, v in updated_todo.dict(exclude_unset=True).items()
            if v is not None
        }

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No valid fields to update"
            )

        update_data["updatedAt"] = datetime.now(
            timezone.utc
        ).isoformat()

        result = await todo_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Todo not found"
            )

        updated = await todo_collection.find_one(
            {"_id": obj_id}
        )

        return {
            "success": True,
            "message": f"Todo with ID {todo_id} updated",
            "data": todo_helper(updated)
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 🔴 DELETE todo
@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    try:
        try:
            obj_id = ObjectId(todo_id)

        except InvalidId:
            raise HTTPException(
                status_code=400,
                detail="Invalid ID format"
            )

        result = await todo_collection.delete_one(
            {"_id": obj_id}
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Todo not found"
            )

        return {
            "success": True,
            "message": "Todo deleted"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )