from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_classic.agents import create_tool_calling_agent
from langchain_classic.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate



# ==================================================
# Load Environment Variables
# ==================================================

load_dotenv()


# ==================================================
# Structured Todo Model
# ==================================================

class SmartTodo(BaseModel):
    title: str
    description: str
    priority: int


# ==================================================
# Gemini LLM
# ==================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2
)

# ==================================================
# Tools
# ==================================================

@tool
def send_email(receiver: str, title: str, body: str):
    """
    this is a send_email tool.
    it invokes when we need to send an email.
    this tool needs 3 parameters:
    - receiver: the email address of the receiver
    - title: the title of the email
    - body: the body of the email
    """

    try:

        print("\n📧 EMAIL TOOL CALLED")
        print(f"To      : {receiver}")
        print(f"Subject : {title}")
        print(f"Body    : {body}")

        return (
            f"Email sent successfully to {receiver} "
            f"with title '{title}'."
        )

    except Exception as e:

        return f"Email sending failed: {str(e)}"


@tool
def ask_receiver_email() -> str:
    """
    This is a ask_receiver_email tool.
    It invokes ONLY when the user wants to send an email but hasn't provided the receiver's email.
    """

    email = input("\n📧 Please provide the receiver's email: ")
    return email

tools = [
    send_email,
    ask_receiver_email
]


agent_prompt = ChatPromptTemplate.from_messages([
    (
        "system",

        """
        #CORE DIRECTIVE
            
        You are an intelligent autonomous Todo Assistant. You must flawlessly understand english, bengali and banglish. 
        Your goal is to process the user input, and extract the core intents, manage different 
        workflows and output a strict, raw and parsable JSON string.


        #WORKFLOWS

        # TODO WORKFLOW
        1. Extract the todo title.
        2. Determine priority.
        3. Generate a description.
        4. Return the todo JSON.

        #EMAIL WORKFLOW
        1. Process the user input and extract the user's intent.
        2. Check if the user explicitly wants to send an email. if yes, then extract these 3 parameters:
            - title: Make it short and meaningful based on the user input
            - body: Generate a professional email body based on the user's intention
            - receiver: identify who the user wants to send the email to.
        3. If the receiver is missing, you must invoke the ask_receiver_email tool to ask the user for it. 
           Suspend all other operations until you get the receiver email.
        4. Once you have all 3 parameters, invoke the send_email tool with the extracted parameters.

        #OUTPUT FORMAT
        Once all tools have finished executing (or if no tools need to be executed), you must output a strict, 
        raw and parsable JSON string with the following format that matches the data model.

        You must follow this exact schema:
        {{
            "title": "Short, clear title of the task",
            "description": "Detailed description of the task, including execution status (e.g., 'Email sent successfully sent to Mira')",
            "priority": <integer> // 1 for low, 2 for medium (default), 3 for high
        }}

        strict rules for output:
        - Do not include any conversational text.
        - Do not include markdown formatting or ```json blocks.
        - Return ONLY the raw, parsable JSON object.
    """
    ),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])




# ==================================================
# Agent Logic
# ==================================================

agent = create_tool_calling_agent(
    llm,
    tools,
    agent_prompt
)

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)



# ==================================================
# Main Loop
# ==================================================

if __name__ == "__main__":

    print("🧠 Smart Todo AI Started!")
    print("Type 'exit' to stop.\n")

    while True:

        user_text = input("Enter todo: ")

        if user_text.lower() == "exit":
            break

        result = executor.invoke({
            "input": user_text
        })

        print("\n✅ Agent Response:")
        print(result["output"])
        print()

    print("\n🧠 Smart Todo AI Stopped.")