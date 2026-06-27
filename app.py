import os
import json
import httpx
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
web_app = FastAPI(
    title="Psi Ψ Smart Tabs Privacy Agent API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Extension and Frontend UI
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARCHIVE_FILE = os.path.join(BASE_DIR, "smart_tabs_archive.json")

# Fixed payload schema to receive both URL and Title directly from extension
class TabPayload(BaseModel):
    url: str
    title: str = "Untitled Isolated Tab"

def get_groq_summary(text_content: str) -> str:
    api_key = "GROQ_API_KEY, YOUR_GROQ_API_KEY_HERE" # Replace with your actual Groq API key
    api_key = api_key.strip()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Analyze the following webpage context. Provide a highly professional one-sentence summary strictly in English focusing on core facts:\n\n{text_content[:3000]}"
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, headers=headers, json=payload)
            
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
        return "Tab archived securely."
    except Exception:
        return "Tab archived securely."

@web_app.get("/")
async def root_redirect():
    return RedirectResponse(url="/docs")

@web_app.post("/archive-tab")
async def archive_tab(tab: TabPayload):
    try:
        # Generate summary using the title directly to prevent request blockage on secure pages
        summary = get_groq_summary(tab.title)
        
        archive_data = []
        if os.path.exists(ARCHIVE_FILE):
            try:
                with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                    archive_data = json.load(f)
            except json.JSONDecodeError:
                archive_data = []

        new_entry = {
            "title": tab.title,
            "url": tab.url,
            "summary": summary
        }
        archive_data.append(new_entry)
        
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=4)
            
        return {"status": "success", "message": f"The tab '{tab.title}' has been safely closed and archived."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Core Error: {str(e)}")

@web_app.get("/search-tabs")
async def search_tabs(query: str = ""):
    if not os.path.exists(ARCHIVE_FILE):
        return {"result": "<div class='text-center text-gray-500 py-8 font-mono text-xs'>Local repository is currently empty.</div>", "data": []}
        
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"result": "<div class='text-center text-red-400 py-8 font-mono text-xs'>Failed to read local data.</div>", "data": []}
        
    if not query:
        return {"result": "<div class='text-center text-gray-500 py-8 font-mono text-xs'>Awaiting centralized query stream commands...</div>", "data": data}
        
    results = []
    filtered_data = []
    for item in data:
        if query.lower() in item['title'].lower() or query.lower() in item['summary'].lower():
            filtered_data.append(item)
            results.append(f"<p class='mb-2'>📍 <b><a href='{item['url']}' target='_blank' class='text-blue-400 underline'>{item['title']}</a></b>: {item['summary']}</p>")
            
    if results:
        return {"result": "".join(results), "data": filtered_data}
    return {"result": "<div class='text-center text-red-400 py-8 font-mono text-xs'>No matching context discovered in local archive.</div>", "data": []}

@web_app.get("/open-in-vscode")
async def open_in_vscode(path: str):
    try:
        clean_path = path.replace("file:///", "").replace("%20", " ")
        if clean_path.startswith('/'):
            clean_path = clean_path.lstrip('/')
            
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        vscode_default_path = os.path.join(local_app_data, "Programs", "Microsoft VS Code", "Code.exe")
        
        if os.path.exists(vscode_default_path):
            subprocess.Popen([vscode_default_path, clean_path], shell=True)
        else:
            subprocess.Popen(["code", clean_path], shell=True)
            
        return {"status": "success", "message": "Opening context inside VS Code Workspace"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))