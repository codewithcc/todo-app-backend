import os
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal, Optional

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate
# Swapped from langchain_openai to langchain_google_genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

# ---------------- LOAD ENV ----------------
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
# Updated to track Google's environment variables safely
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "❌ CRITICAL ERROR: 'GOOGLE_API_KEY' or 'GEMINI_API_KEY' is missing! "
        f"Please check that your .env file exists in: {base_dir} and contains GOOGLE_API_KEY=AIzaSy..."
    )

# ---------------- DB SETUP ----------------
client = AsyncIOMotorClient(MONGODB_URI)
db = client["ai-todo-app"]
todo_collection = db["todos"]


# ---------------- LIFESPAN (STARTUP/SHUTDOWN) ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    yield
    print("🛑 Shutting down backend application...")


# ---------------- APP ----------------
app = FastAPI(title="AI Todo API", version="1.0.0", lifespan=lifespan)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- AI OUTPUT SCHEMA ----------------
class SmartTodoOutput(BaseModel):
    title: str = Field(description="Short, action-oriented task title summary.")
    description: Optional[str] = Field(default=None, description="Extra background details or context if present.")
    checked: bool = Field(default=False, description="Completion state of the task.")


# ---------------- EMAIL TOOL PART ----------------
@tool
def send_email(receiver: str, title: str, body: str) -> str:
    """
    Send an email to a receiver with a specific title (subject) and body content.
    Use this tool ONLY when the user explicitly asks to send an email or message to someone.
    """
    output = f"An email with {title} and {body} is send to {receiver}."
    print(f"\n[Tool Action] {output}")
    return output


# ---------------- AI SETUP ----------------
# Swapped to Google's gemini-2.5-flash with your Google API Key
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0.2, api_key=GEMINI_API_KEY
)

# Bind both tools into a parallel evaluation state for Google tool-use routing
llm_with_tools = llm.bind_tools([SmartTodoOutput, send_email])

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an intelligent AI Assistant capable of managing todos and sending emails.

Your primary job is to convert human language into structured todo items using the SmartTodoOutput tool.
However, if the user explicitly requests to send an email, call the `send_email` tool instead.

Rules for Todo items:
- Keep the title short and actionable
- Description should contain extra details if present
- checked should default to false
""",
        ),
        ("human", "{text}"),
    ]
)


# ---------------- REQUEST MODELS ----------------
class TodoCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    checked: bool = False


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    checked: Optional[bool] = None


class SmartTodoRequest(BaseModel):
    text: str = Field(min_length=1)


# ---------------- HELPERS ----------------
def todo_helper(todo) -> dict:
    return {
        "id": str(todo["_id"]),
        "title": todo.get("title"),
        "description": todo.get("description"),
        "checked": todo.get("checked", False),
        "createdAt": (
            todo.get("createdAt").isoformat()
            if isinstance(todo.get("createdAt"), datetime)
            else None
        ),
        "updatedAt": (
            todo.get("updatedAt").isoformat()
            if isinstance(todo.get("updatedAt"), datetime)
            else None
        ),
    }


def validate_object_id(todo_id: str) -> ObjectId:
    try:
        return ObjectId(todo_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")


# ---------------- ROUTES ----------------


# 🟢 GET ALL TODOS
@app.get("/todos")
async def get_todos():
    todos = await todo_collection.find().to_list(length=None)
    return {
        "success": True,
        "count": len(todos),
        "data": [todo_helper(todo) for todo in todos],
    }


# 🤖 SMART TODO & EMAIL ROUTER ENDPOINT
@app.post("/todos/smart", status_code=201)
async def create_smart_todo(payload: SmartTodoRequest):
    chain = prompt | llm_with_tools
    ai_result = await chain.ainvoke({"text": payload.text})

    # Validate if the Gemini model routed to a tool execution block
    if hasattr(ai_result, "tool_calls") and ai_result.tool_calls:
        tool_call = ai_result.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # Scenario A: User wants an email processed
        if tool_name == "send_email":
            tool_output = send_email.invoke(tool_args)
            return {
                "success": True,
                "type": "email_action",
                "message": "Email action executed successfully",
                "data": {"output": tool_output}
            }
        
        # Scenario B: User input evaluates to a standard structured Todo
        elif tool_name == "SmartTodoOutput":
            now = datetime.now(timezone.utc)
            todo_data = {
                "title": tool_args.get("title"),
                "description": tool_args.get("description"),
                "checked": tool_args.get("checked", False),
                "createdAt": now,
                "updatedAt": now,
            }
            result = await todo_collection.insert_one(todo_data)
            created = await todo_collection.find_one({"_id": result.inserted_id})
            
            return {
                "success": True,
                "type": "todo_creation",
                "message": "Smart todo created",
                "data": todo_helper(created),
            }

    # Fallback response if parsing doesn't touch parameters clearly
    raise HTTPException(
        status_code=422, 
        detail="Unable to securely isolate an email task or a todo item structure from the input provided."
    )


# 🔵 GET SINGLE TODO
@app.get("/todos/{todo_id}")
async def get_todo(todo_id: str = Path(...)):
    obj_id = validate_object_id(todo_id)
    todo = await todo_collection.find_one({"_id": obj_id})

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"success": True, "data": todo_helper(todo)}


# 🟣 CREATE TODO (MANUAL)
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
        "data": todo_helper(created),
    }


# 🟡 UPDATE TODO
@app.patch("/todos/{todo_id}")
async def update_todo(todo_id: str = Path(...), todo: TodoUpdate = None):
    obj_id = validate_object_id(todo_id)
    update_data = todo.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    update_data["updatedAt"] = datetime.now(timezone.utc)

    result = await todo_collection.update_one(
        {"_id": obj_id}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found")

    updated = await todo_collection.find_one({"_id": obj_id})

    return {
        "success": True,
        "message": "Updated successfully",
        "data": todo_helper(updated),
    }


# 🔴 DELETE TODO
@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str = Path(...)):
    obj_id = validate_object_id(todo_id)
    result = await todo_collection.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"success": True, "message": "Deleted successfully"}


# ---------------- SERVER RUNNER ----------------
if __name__ == "__main__":
    import uvicorn

    print("\n🚀 Starting the AI Todo API Server (Gemini Powered)...")
    print("📋 API Documentation available at: http://127.0.0.1:8000/docs\n")

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
