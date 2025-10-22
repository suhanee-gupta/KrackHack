import os
import git
import subprocess
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
# from app.routes import auth
from app.routes import auth
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GEMINI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# External API URLs (No API Key Needed)
DESIGNER_AGENT_URL = os.getenv("DESIGNER_AGENT_URL")
DEVELOPER_AGENT_URL = os.getenv("DEVELOPER_AGENT_URL")
PROJECT_MANAGER_KEY = os.getenv("PROJECT_MANAGER_KEY")

GIT_REPO_URL = "https://github.com/Ojasvi310/PixelForge.git"
LOCAL_REPO_PATH = "generated_project"

app = FastAPI()
app.include_router(auth.router, prefix="/auth")

def call_ai_agent(url, request_text): 
    headers = {"Content-Type": "application/json"}
    data = {"prompt_file": request_text}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def call_designer_agent(prompt):
    ui_json = call_ai_agent(DESIGNER_AGENT_URL, prompt)
    return ui_json

def call_ai_agent_for_developer(url, request_json, design_json):
    # print(url,request_json,design_json)
    headers = {"Content-Type": "application/json"}
    data = {"prompt_file": request_json,"design_files":design_json}  # Replace with actual input
    response = requests.post(url, json=data, headers=headers)
    # print("Status Code:", response.status_code)
    # print("Response:", response.json())  # If response is JSON
    return response.json()

def call_developer_agent(request_json, ui_json):
    response = call_ai_agent_for_developer(DEVELOPER_AGENT_URL, request_json, ui_json)
    return response

designer_tool = Tool(name="UI Designer", func=call_designer_agent, description="Generates UI/UX JSON")
developer_tool = Tool(name="Code Generator", func=call_developer_agent, description="Converts UI JSON to Code JSON")

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

from langchain.llms.base import LLM

llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GEMINI_API_KEY)

coordinator_agent = initialize_agent(
    tools=[designer_tool, developer_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory
)
# LOCAL_REPO_PATH="D:/GitTemp"
# def save_code_to_files(code_json):
#     os.makedirs(LOCAL_REPO_PATH, exist_ok=True)
#     for filename, content in code_json.items():
#         with open(os.path.join(LOCAL_REPO_PATH, filename), "w") as f:
#             f.write(content)

def push_to_github():
    if not os.path.exists(os.path.join(LOCAL_REPO_PATH, ".git")):
        repo = git.Repo.init(LOCAL_REPO_PATH)
        origin = repo.create_remote("origin", GIT_REPO_URL)
    else:
        repo = git.Repo(LOCAL_REPO_PATH)
        origin = repo.remotes.origin
    repo.git.add(all=True)
    repo.index.commit("Auto-generated project files from LLaMA 3")
    origin.push()

@app.post("/generate-website/")
async def generate_website(request_text):
    """Main API to generate a website using the multi-agent system."""
    try:
        ui_json = call_designer_agent(request_text)
        if "error" in ui_json:
            return {"error": "UI design generation failed"}

        code_json = call_developer_agent(request_text, ui_json)
        if "error" in code_json:
            return {"error": "Code generation failed"}

        # # Step 4: Save & Push to GitHub
        # final_code = fixed_code_json if retries > 0 else code_json
        # save_code_to_files(final_code)
        # push_to_github() 

        return {
            "ui_design": ui_json,
            "generated_code": code_json,
            # "test_result": test_result,
            # "retries": retries,
            # "github_status": "Pushed to GitHub successfully"
        }

    except Exception as e:
        return {"error": str(e)}
