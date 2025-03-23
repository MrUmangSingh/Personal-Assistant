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

class Orion:
    def __init__(self):
        load_dotenv()
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(model_name="llama-3.3-70b-versatile")
        self.system_message = self.generate_system_message()
        self.memory = MemorySaver()
        self.tools = [self.reading_email, self.sending_email, self.tweet]
        self.llm_with_tool = self.llm.bind_tools(self.tools)
        self.app = self.build_workflow()
        
    def generate_system_message(self):
        return f"""You are Orion, a highly capable and friendly AI personal assistant. Your primary responsibilities include:  
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
                {datetime.now()}

                ### **User:**  
                User's name is *Umang Singh*.  

                Always ensure your responses are clear, helpful, and aligned with Umang's needs.
                """

    @tool
    def reading_email(self, tag: str) -> dict:
        """Search the recent mails based on tag provided."""
        read = ReadEmail()
        service = read.service
        results = read.search_messages(service, tag, max_results=2)

        message_data = {}
        for i, msg in enumerate(results):
            msg_details = read.read_message(service, msg)
            message_data[f"Email_{i+1}"] = msg_details
        return message_data

    @tool
    def sending_email(self, email: str, subject: str, body: str) -> str:
        """Send an email to the provided email address with a given subject and body."""
        send_email = SendEmail()
        service = send_email.service
        send_email.send_message(service, email, subject, body)
        return "Mail sent successfully"

    @tool(return_direct=True)
    def tweet(self, message: str) -> str:
        """Tweet the message provided if you are asked for tweeting only."""
        tweet = TwitterPost()
        tweet.make_tweet(message)
        return "Tweeted successfully"

    def call_model(self, state: MessagesState):
        messages = state['messages']
        response = self.llm_with_tool.invoke(messages)
        return {"messages": [response]}

    def router(self, state: MessagesState) -> Literal["tools", END]: # type: ignore
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    def build_workflow(self):
        workflow = StateGraph(MessagesState)
        workflow.add_node("Agent", self.call_model)
        workflow.add_node("Tools", ToolNode(self.tools))
        workflow.add_edge(START, "Agent")
        workflow.add_conditional_edges("Agent", self.router, {
            "tools": "Tools",
            END: END
        })
        workflow.add_edge("Tools", "Agent")
        return workflow.compile(checkpointer=self.memory)

    def chat(self, user_input: str):
        config = {"configurable": {"thread_id": "1"}}
        response = self.app.invoke({"messages": [
            self.system_message, user_input
        ]}, config)
        return response['messages'][-1].content


if __name__ == "__main__":
    orion = Orion()
    
    while True:
        chat = input("YOU: ")
        if chat.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        response = orion.chat(chat)
        print("ORION: " + response)
