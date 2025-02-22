# from fastapi import FastAPI
# from app.routes import auth

# app = FastAPI()
# app.include_router(auth.router, prefix="/auth")

import os
import git
import subprocess
from fastapi import FastAPI, WebSocket
from app.routes import auth
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from langchain_community.llms import HuggingFaceHub


prompt="Create a photo gallery website"

# Load API Keys (Only for LLaMA 3, not Agent.ai)
HF_API_KEY = os.getenv("HF_API_KEY", "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")

# External API URLs (No API Key Needed)
DESIGNER_AGENT_URL = "https://api-lr.agent.ai/v1/agent/k1mctw3deuvs1dp0/webhook/241457d0"
DEVELOPER_AGENT_URL = "https://api-lr.agent.ai/v1/agent/ethcni1fsprxwt12/webhook/826fbddb"

# Git Configuration
GIT_REPO_URL = "https://github.com/Ojasvi310/PixelForge.git"
LOCAL_REPO_PATH = "generated_project"

# Initialize FastAPI
app = FastAPI()

app.include_router(auth.router, prefix="/auth")

# Initialize LLaMA 3 (LLM for Coordination & Testing)
llm = HuggingFaceHub(
    repo_id="meta-llama/Llama-3.3-70B-Instruct",
    model_kwargs={"temperature": 0.7, "max_new_tokens": 500},
    huggingfacehub_api_token=HF_API_KEY
)

# Function to call AI agents using curl
def call_ai_agent(url, request_json):
    """Sends a JSON request to an AI agent using curl."""
    curl_command = [
        "curl", "-X", "POST", "-H", "Content-Type: application/json",
        "-d", request_json, url
    ]
    result = subprocess.run(curl_command, capture_output=True, text=True)
    return result.stdout

def call_designer_agent(prompt):
    """Calls the Designer Agent using curl to generate UI/UX JSON."""
    request_json = f'{{"prompt": "{prompt}"}}'
    response = call_ai_agent(DESIGNER_AGENT_URL, request_json)
    return response

def call_ai_agent_for_developer(url, request_json, design_json):
    # """Sends a JSON request to an AI agent using curl."""
    # curl_command = [
    #     "curl", "-X", "POST", "-H", "Content-Type: application/json",
    #     "-d", request_json, url, "-d", design_json, url
    # ]
    # result = subprocess.run(curl_command, capture_output=True, text=True)
    # return result.stdout

    """Sends two files to an AI agent using curl."""
    curl_command = [
        "curl", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-F", f"request=@{request_json}",
        "-F", f"design=@{design_json}",
        url
    ]
    
    result = subprocess.run(curl_command, capture_output=True, text=True)
    return result.stdout


# Define Tools (Calls Agent.ai Without API Key)


def call_developer_agent(ui_json):
    """Calls the Developer Agent using curl to generate code JSON."""
    request_json = f'{{"ui_design": {ui_json}}}'
    response = call_ai_agent_for_developer(DEVELOPER_AGENT_URL, request_json, call_designer_agent(prompt))
    return response

designer_tool = Tool(name="UI Designer", func=call_designer_agent, description="Generates UI/UX JSON")
developer_tool = Tool(name="Code Generator", func=call_developer_agent, description="Converts UI JSON to Code JSON")

# Initialize LangChain Memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# LLaMA 3 Coordinating Agent
coordinator_agent = initialize_agent(
    tools=[designer_tool, developer_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory
)

# Function to save generated code to local files
def save_code_to_files(code_json):
    os.makedirs(LOCAL_REPO_PATH, exist_ok=True)
    for filename, content in code_json.items():
        with open(os.path.join(LOCAL_REPO_PATH, filename), "w") as f:
            f.write(content)

# Function to push to GitHub
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
async def generate_website(user_prompt: str):
    """Main API to generate a website using the multi-agent system."""
    try:
        # Step 1: Generate UI/UX JSON using curl
        ui_json = call_designer_agent(user_prompt)
        if "error" in ui_json:
            return {"error": "UI design generation failed"}

        # Step 2: Generate Code JSON using curl
        code_json = call_developer_agent(ui_json)
        if "error" in code_json:
            return {"error": "Code generation failed"}

        # Step 3: LLM Performs Testing & Debugging
        max_retries = 3
        retries = 0
        test_result = coordinator_agent.run(f"Test this generated code and report any errors:\n{code_json}")

        while "error" in test_result and retries < max_retries:
            retries += 1
            correction_prompt = f"Fix the errors in this code:\n{code_json}\nErrors found: {test_result}"
            fixed_code_json = coordinator_agent.run(correction_prompt)
            test_result = coordinator_agent.run(f"Re-test this fixed code:\n{fixed_code_json}")

        # Step 4: Save & Push to GitHub
        final_code = fixed_code_json if retries > 0 else code_json
        save_code_to_files(final_code)  # Save the generated files
        push_to_github()  # Push the project to GitHub

        return {
            "ui_design": ui_json,
            "generated_code": final_code,
            "test_result": test_result,
            "retries": retries,
            "github_status": "Pushed to GitHub successfully"
        }

    except Exception as e:
        return {"error": str(e)}

# WebSocket for Real-time Updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            response = coordinator_agent.run(data)
            await websocket.send_text(response)
    except Exception as e:
        await websocket.send_text(str(e))