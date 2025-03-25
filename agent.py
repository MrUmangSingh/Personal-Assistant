from langchain_groq import ChatGroq
import os
from langchain_core.tools import tool
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from typing import Literal
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from ReadEmail import ReadEmail
from SendEmail import SendEmail
from TwitterPost import TwitterPost
from datetime import datetime

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model_name="llama-3.3-70b-versatile")


system_message = """You are Orion, a highly capable and friendly AI personal assistant. Your primary responsibilities include:  
1. **Sending Emails** – While sending emails to users with proper formatting like salutation and closing of the mail.
2. **Handling Twitter Posts** – Posting tweets and managing Twitter interactions professionally.  
3. **Conversing Naturally** – Responding in a friendly and helpful manner while ensuring clarity and accuracy.  

### **Guidelines for Your Behavior:**
- Always respond **politely and informatively**, keeping interactions warm and engaging.  
- Use **today's date and time** to provide relevant information (e.g., scheduling emails, setting reminders).  
- When **managing emails**, be mindful of time-sensitive messages and summarize key details if asked.  
- When **posting on Twitter**, ensure the content is appropriate, concise, and engaging.  
- If the user simply greets you (e.g., "Hi"), reply in a **friendly, conversational** way rather than calling a tool.  
- Only **use tools** (email, Twitter, etc.) when explicitly asked to take action.  

### **Current Date & Time:**  
{{current_datetime}}

### **User:**  
User's name is *Umang Singh*.  

Always ensure your responses are clear, helpful, and aligned with Umang's needs.  
""".format(current_datetime=datetime.now())

memory = MemorySaver()


@tool
def reading_email(tag: str) -> dict:
    """Search the recent mails based on tag provided."""
    read = ReadEmail()
    service = read.service
    results = read.search_messages(service, tag, max_results=2)

    message_data = {}
    for i, msg in enumerate(results):
        msg_details = read.read_message(service, msg)
        message_data[f"Email_{i+1}"] = msg_details
    return message_data


# email_data = reading_email.invoke("Scheduled class")
# print(email_data)

@tool
def sending_email(email: str, subject: str, body: str) -> str:
    """Send an email to the provided email address with a given subject and body."""
    send_email = SendEmail()
    service = send_email.service
    send_email.send_message(service, email, subject, body)
    return "Tell user that mail sent successfully"


# send = sending_email.invoke({
#     "email": "unknownsstark@gmail.com",
#     "subject": "Test Subject",
#     "body": "Hiii, This is a test email"
# })
# print(send)

@tool(return_direct=True)
def tweet(message: str) -> str:
    """Tweet the message provided if you are asked for tweeting only."""
    tweet = TwitterPost()
    tweet.make_tweet(message)
    return "Tweeted successfully"


# print(tweet.invoke("Tweeted from agent"))

tools = [reading_email, sending_email, tweet]

llm_with_tool = llm.bind_tools(tools)

# print(llm_with_tool.invoke(
#     "send an email to unknownsstark@gmail.com with subject as LLM is working, and body as Hiii, This is a Orion"))


def call_model(state: MessagesState):
    messages = state['messages']
    response = llm_with_tool.invoke(messages)
    return {"messages": [response]}


# response = call_model({"messages": [
#                       system_message, "Tweet a message regarding how todays industry is growing"]})


# print(response["messages"][-1].tool_calls)

def router(state: MessagesState) -> Literal["tools", END]:  # type: ignore
    messages = state['messages']
    last_message = messages[-1]
    print(f"--------Last message--------- {last_message}")
    if last_message.tool_calls:
        return "tools"
    return END


workflow = StateGraph(MessagesState)
workflow.add_node("Agent", call_model)
workflow.add_node("Tools", ToolNode(tools))
workflow.add_edge(START, "Agent")
workflow.add_conditional_edges("Agent", router, {
    "tools": "Tools",
    END: END
})
workflow.add_edge("Tools", "Agent")
app = workflow.compile(checkpointer=memory)


config = {"configurable": {"thread_id": "1"}}


# for s in app.stream({
#         "messages": [system_message, "send an email to unknownsstark@gmail.com telling him that i won't be coming in tomorrow's meeting"]}, config):
#     if "__end__" not in s:
#         print(s)
#         print("----")

class Orion:
    def __init__(self):
        pass

    def chat(self, message: str) -> str:
        response = app.invoke({"messages": [system_message, message]}, config)
        return response["messages"][-1].content


if __name__ == '__main__':
    orion = Orion()
    while True:
        chat = input("YOU: ")
        response = orion.chat(chat)

        print("ORION: " + response)
