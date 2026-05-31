import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# 1. Load environment variables from .env file
load_dotenv()

# 2. Strict Structured Output Model
class SmartTodo(BaseModel):
    title: str = Field(..., description="Short, clean, and meaningful title of the task translated to English.")
    date: Optional[str] = Field(None, description="Readable date/time expression. Use null if impossible to determine.")
    priority: Literal["low", "medium", "high"] = Field(..., description="The priority level of the task.")

# 3. Initialize Google Generative AI model
# Looks for GOOGLE_API_KEY or GEMINI_API_KEY in your environment/.env file
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

# Force structured output using Pydantic schema
structured_llm = llm.with_structured_output(SmartTodo)

# 4. Prompt Template with multi-lingual examples
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an intelligent AI Todo Extraction Assistant.
Your job is to convert messy human language into structured todo data.

The user may write:
- informal English
- Bengali written in English letters (Banglish)
- mixed English + Bengali
- incomplete sentences
- casual human speech

You must intelligently understand the meaning and extract structured information.

Rules:
1. Keep the title short, clean, and meaningful. Always translate/summarize the title into clear English.
2. Convert informal date/time expressions into readable text.
Examples:
- "kal" → "Tomorrow"
- "aj rat 9tay" → "Tonight 9 PM"
- "Friday te 12pm" → "Friday 12 PM"
3. Priority must only be: 'low', 'medium', or 'high'.
4. If priority is explicitly mentioned, use it.
5. If priority is NOT mentioned, infer it from the context:
   - Urgent work, deadlines, exams, meetings, submissions → high
   - Normal daily tasks → medium
   - Entertainment, hangout, movies, casual plans → low
   - If still unclear → use medium
6. If date/time is not mentioned clearly, use a reasonable interpretation when possible. If impossible to determine, return null.
7. Return only structured todo information matching the schema.

Examples:

Input: "Friday te 12pm e internal ache computer architect er, high priority"
Output: {{ "title": "Computer Architecture Internal", "date": "Friday 12 PM", "priority": "high" }}

Input: "Group meeting tomorrow at 2 PM, medium priority"
Output: {{ "title": "Group meeting", "date": "Tomorrow 2 PM", "priority": "medium" }}

Input: "Doctor appointment tomorrow at 5 PM"
Output: {{ "title": "Doctor appointment", "date": "Tomorrow 5 PM", "priority": "medium" }}

Input: "Aj rat 9tay assignment complete korte hobe, priority high"
Output: {{ "title": "Complete assignment", "date": "Tonight 9 PM", "priority": "high" }}

Input: "Aj ami bondhu der sathe movie dekhbo"
Output: {{ "title": "Watch movie with friends", "date": "Tonight", "priority": "low" }}

Input: "Saturday ami amr friends sthe ghurte jbo"
Output: {{ "title": "Hangout with friends", "date": "Saturday", "priority": "low" }}

Input: "Kal final project submit korte hobe"
Output: {{ "title": "Final project submission", "date": "Tomorrow", "priority": "high" }}
"""),
    ("human", "{input}")
])

# 5. Core AI function with correct formatting logic
def extract_todo(user_text: str) -> SmartTodo:
    # Safely formats into a PromptValue object that structured_llm accepts natively
    formatted_prompt = prompt.format_prompt(input=user_text)
    result = structured_llm.invoke(formatted_prompt)
    return result

# 6. Interactive CLI Loop
if __name__ == "__main__":
    print("🧠 Smart Todo AI Started!")
    
    # Simple check to alert you if the API key isn't being loaded properly
    has_key = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    print(f"🔑 API Key Detected: {'✅ YES' if has_key else '❌ NO (Check your .env file)'}")
    print("Type 'exit' to stop.\n")

    while True:
        user_text = input("Enter todo: ")
        
        if user_text.lower().strip() == "exit":
            print("\n👋 Exiting Smart Todo AI...")
            break
        
        if not user_text.strip():
            continue

        try:
            result = extract_todo(user_text)
            print("\n--- AI OUTPUT ---")
            # Using .model_dump() (Pydantic v2) or .dict() to display nicely
            print(result.model_dump())
            print()
        except Exception as e:
            print(f"\n❌ Error processing input: {e}\n")
