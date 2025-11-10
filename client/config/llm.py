from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from dotenv import load_dotenv
import os
load_dotenv()
from config.env import EnvConfig
from api.client import client

env = EnvConfig()
gemini_api_key = os.getenv("GEMINI_API_KEY")

async def getModel():
    geminiModel = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        api_key=gemini_api_key  
    )
    
    tools = await client.get_tools()
    geminiAgent = create_agent(geminiModel, tools)
    
    return geminiAgent  