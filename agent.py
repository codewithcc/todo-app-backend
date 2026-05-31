from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.messages import HumanMessage


# 🔹 Load environment variables
load_dotenv()


# 🔹 Structured output model
class SmartTodo(BaseModel):
    title: str
    date: str
    priority: str
    needs_email: bool


# 🔹 Google Generative AI model
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)


# 🔹 Force structured output
structured_llm = llm.with_structured_output(SmartTodo)

#an email tool
@tool
def send_email(receiver: str, title: str, body: str):
    """
    Mock email sender.
    """

    message = (
        f"An email with '{title}' "
        f"and '{body}' "
        f"is sent to {receiver}"
    )

    print("\n📧 EMAIL TOOL CALLED")
    print(message)

    return message

#email tool bound llm
email_llm = llm.bind_tools([send_email])

def handle_email_request(user_text: str):

    response = email_llm.invoke(
        [HumanMessage(content=user_text)]
    )

    if response.tool_calls:

        for tool_call in response.tool_calls:

            if tool_call["name"] == "send_email":

                send_email.invoke(tool_call["args"])

                return "Email tool executed."

    return response.content


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
- needs_email

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
     
10. Determine if the task requires an email reminder.

Set needs_email:

- true:
  meetings
  client calls
  interviews
  professional discussions
  project reviews
  important office events

- false:
  personal tasks
  shopping
  movies
  hangouts
  hobbies
  entertainment


"""),

    ("human", "{input}")
])



# 🔹 Main AI function
def extract_todo(user_text: str):

    formatted_prompt = prompt.format_messages(
        input=user_text
    )

    return structured_llm.invoke(formatted_prompt)


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

        print("\n--- TODO OUTPUT ---")
        print(result)

        if result.needs_email:

            print(
                "\n🤖 AI thinks this task may require "
                "an email reminder."
            )

            email = input(
                "📧 Enter receiver email "
                "(leave blank to skip): "
            )

            if email.strip():

                send_email.invoke({
                    "receiver": email,
                    "title": result.title,
                    "body": (
                        f"Reminder: "
                        f"{result.title} "
                        f"on {result.date}"
                    )
                })

        print()