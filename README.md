# TODO App CRUD operations (using MongoDB)

## Create mongodb local database and collection
If no mongodb cluster/connection created then create a local connection and create a database called `ai-todo-app` then inside of the database create a collection `todos`. Click on the 3-dots of the conection and copy the connection string/mongodb url

## Add Mongodb connection URL into .env.local file
```bash
MONGODB_URL=your_mongodb_url
```

## Import required modules
```python
from fastapi import FastAPI, HTTPException  
from pydantic import BaseModel  
import pymongo  
import os  
from dotenv import load_dotenv  
from datetime import datetime, timezone  
from bson import ObjectId  
from bson.errors import InvalidId
```

## Create FastAPI instance
```python
app = FastAPI()
```

## Load enviroment variables
```python
load_dotenv()
```

## Initialize mongodb driver
```python
client = pymongo.MongoClient(os.getenv("MONGODB_URI"))  
db = client.get_database("ai-todo-app")  
collection = db.get_collection("todos")
```

## Create TODO schema
```python
class Todo(BaseModel):
	title: str | None = None
	description: str | None = None
	checked: bool | None = None
```

## GET request to fetch all TODOs from database - `/todos`
```python
@app.get("/todos")  
def get_todos():  
    try:  
        data = []  
        for doc in collection.find():  
            doc["_id"] = str(doc["_id"])  
            data.append(doc)  
        return {"success": True, "data": data}  
    except HTTPException as e:  
        raise e  
    except Exception:  
        raise HTTPException(500, "Internal server error")
```

## GET request to fetch particular TODO from database having id as `todo_id` - `/todos/{todo_id}`
```python
@app.get("/todos/{todo_id}")  
def get_todo(todo_id: str):  
    try:  
        try: obj_id = ObjectId(todo_id)  
        except InvalidId: raise HTTPException(400, "Given object-id is invalid.")  
  
        data = collection.find_one({"_id": obj_id})  
        if not data: raise HTTPException(404, f"No todo found with id:{todo_id}")  
  
        data["_id"] = str(data["_id"])  
        return {"success": True, "data": data}  
    except HTTPException as e:  
        raise e  
    except Exception:  
        raise HTTPException(500, "Internal server error")
```

## POST request to create new todo in database - `/todos`
```python
@app.post("/todos")  
def create_todo(todo: Todo):  
    try:  
        raw_data = {k: v for k, v in todo.model_dump().items() if v is not None}  
        if not raw_data: raise HTTPException(400, "Given request body containing null values!")  
  
        raw_data["createdAt"] = datetime.now(timezone.utc).isoformat()  
        raw_data["updatedAt"] = datetime.now(timezone.utc).isoformat()  
        data = collection.insert_one(raw_data)  
  
        return {"success": True, "message": f"New todo inserted with id:{data.inserted_id}"}  
    except HTTPException as e:  
        raise e  
    except Exception:  
        raise HTTPException(500, "Internal server error")
```

## PATCH request to update a TODO in database having id as `todo_id` - `/todos/{todo_id}`
```python
@app.patch("/todos/{todo_id}")  
def update_todo(todo_id: str, todo: Todo):  
    try:  
        try: obj_id = ObjectId(todo_id)  
        except InvalidId: raise HTTPException(400, "Given object-id is invalid.")  
  
        raw_data = {k: v for k, v in todo.model_dump().items() if v is not None}  
        if not raw_data: raise HTTPException(400, "Given request body containing null values!")  
  
        raw_data["updatedAt"] = datetime.now(timezone.utc).isoformat()  
        data = collection.find_one_and_update({"_id": obj_id}, {"$set": raw_data})  
  
        if data.matched_count == 0: raise HTTPException(404, f"No item found with id:{todo_id}.")  
  
        return {"success": True, "message": f"Todo with ID:{todo_id} updated!"}  
    except HTTPException as e:  
        raise e  
    except Exception:  
        raise HTTPException(500, "Internal server error")
```

## DELETE request to delete a TODO from database having id as `todo_id` - `/todos/{todo_id}`
```python
@app.delete("/todos/{todo_id}")  
def delete_todo(todo_id: str):  
    try:  
        try: obj_id = ObjectId(todo_id)  
        except InvalidId: raise HTTPException(400, "Given object-id is invalid.")  
  
        data = collection.find_one_and_delete({"_id": obj_id})  
        if data.deleted_count == 0: raise HTTPException(404, f"No item found with id:{todo_id}.")  
  
        return {"success": True, "message": f"Todo with ID:{todo_id} deleted!"}  
    except HTTPException as e:  
        raise e  
    except Exception:  
        raise HTTPException(500, "Internal server error")
```

## Test the APIs
Start the FastAPI
```bash
fastapi dev
```
Click this link - [https://127.0.0.1:8000/docs](https://127.0.0.1:8000/docs)