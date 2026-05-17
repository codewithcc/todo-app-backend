from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid

app = FastAPI()

# 🔹 Todo Schema (combined + improved)
class Todo(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    checked: bool = False

# 🔹 In-memory database
todos: List[Todo] = []

# 🟢 GET all todos
@app.get("/todos")
def get_todos():
    try:
        return {"success": True, "data": todos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔵 GET single todo
@app.get("/todos/{todo_id}")
def get_todo(todo_id: str):
    try:
        for todo in todos:
            if todo.id == todo_id:
                return {"success": True, "data": todo}
        raise HTTPException(status_code=404, detail="Todo not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🟣 POST create todo
@app.post("/todos")
def create_todo(todo: Todo):
    try:
        todo.id = str(uuid.uuid4())  # unique ID
        todos.append(todo)
        return {"success": True, "data": todo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🟡 PATCH update todo
@app.patch("/todos/{todo_id}")
def update_todo(todo_id: str, updated_todo: Todo):
    try:
        for idx, todo in enumerate(todos):
            if todo.id == todo_id:
                updated_data = updated_todo.dict(exclude_unset=True)

                if "title" in updated_data:
                    todos[idx].title = updated_data["title"]
                if "description" in updated_data:
                    todos[idx].description = updated_data["description"]
                if "checked" in updated_data:
                    todos[idx].checked = updated_data["checked"]

                return {
                    "success": True,
                    "message": f"Todo with ID {todo_id} updated",
                    "data": todos[idx]
                }

        raise HTTPException(status_code=404, detail="Todo not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔴 DELETE todo
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    try:
        for idx, todo in enumerate(todos):
            if todo.id == todo_id:
                deleted = todos.pop(idx)
                return {
                    "success": True,
                    "message": f"Todo with ID {todo_id} deleted",
                    "data": deleted
                }

        raise HTTPException(status_code=404, detail="Todo not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))