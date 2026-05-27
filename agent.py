from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv


# 🔹 Load environment variables
load_dotenv()


# 🔹 Structured output model
class SmartTodo(BaseModel):
    title: str
    date: str
    priority: str


# 🔹 Google Generative AI model
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

# 🔹 Force structured output
structured_llm = llm.with_structured_output(SmartTodo)


# 🔹 Prompt Template with examples


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

You must extract:
- title
- date
- priority

Rules:

1. Keep the title short, clean, and meaningful.

2. Convert informal date/time expressions into readable text.
Examples:
- "kal" → "Tomorrow"
- "aj rat 9tay" → "Tonight 9 PM"
- "Friday te 12pm" → "Friday 12 PM"

3. Priority must only be:
- low
- medium
- high

4. If priority is explicitly mentioned, use it.

5. If priority is NOT mentioned:
- infer it from the task context
- urgent work, deadlines, exams, meetings, submissions → high
- normal daily tasks → medium
- entertainment, hangout, movies, casual plans → low
- if still unclear → use medium

6. If date/time is not mentioned clearly, use a reasonable interpretation when possible.
If impossible to determine, return null.

7. Return only structured todo information.

8. Do not add explanations.

9. Understand both English and Bengali mixed language naturally.

Examples:

Input:
"Friday te 12pm e internal ache computer architect er, high priority"

Output:
{{
    "title": "Computer Architecture Internal",
    "date": "Friday 12 PM",
    "priority": "high"
}}

Input:
"Group meeting tomorrow at 2 PM, medium priority"

Output:
{{
    "title": "Group meeting",
    "date": "Tomorrow 2 PM",
    "priority": "medium"
}}

Input:
"Doctor appointment tomorrow at 5 PM"

Output:
{{
    "title": "Doctor appointment",
    "date": "Tomorrow 5 PM",
    "priority": "medium"
}}

Input:
"Aj rat 9tay assignment complete korte hobe, priority high"

Output:
{{
    "title": "Complete assignment",
    "date": "Tonight 9 PM",
    "priority": "high"
}}

Input:
"Aj ami bondhu der sathe movie dekhbo"

Output:
{{
    "title": "Watch movie with friends",
    "date": "Tonight",
    "priority": "low"
}}

Input:
"Saturday ami amr friends sthe ghurte jbo"

Output:
{{
    "title": "Hangout with friends",
    "date": "Saturday",
    "priority": "low"
}}

Input:
"Kal final project submit korte hobe"

Output:
{{
    "title": "Final project submission",
    "date": "Tomorrow",
    "priority": "high"
}}

"""),

    ("human", "{input}")
])



# 🔹 Main AI function
def extract_todo(user_text: str):

    formatted_prompt = prompt.format_messages(
        input=user_text
    )

    result = structured_llm.invoke(formatted_prompt)

    return result


# 🔹 Test the AI
if __name__ == "__main__":

    print("🧠 Smart Todo AI Started!")
    print("Type 'exit' to stop.\n")

    while True:

        user_text = input("Enter todo: ")

        if user_text.lower() == "exit":
            print("\n👋 Exiting Smart Todo AI...")
            break

        result = extract_todo(user_text)

        print("\n--- AI OUTPUT ---")
        print(result)
        print()