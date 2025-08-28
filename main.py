import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("--- main.py loading ---")

import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from scribby_pi.agent import ScribbyAgent
from scribby_pi.config import (
    CORPUS_DIR,
    INDEX_DIR,
    NOTES_DIR,
    LOG_DIR as LIFE_LOG_DIR,
    EMBEDDING_MODEL,
    LLM_MODEL,
    AGENT_NAME,
    NUM_RESEARCH_CHUNKS,
)

# --- Agent and App Setup ---
app = FastAPI()

# Mount static files directory
static_dir = Path(__file__).parent / "scribby_pi" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

agent = ScribbyAgent(
    name=AGENT_NAME,
    corpus_dir=Path(CORPUS_DIR),
    index_dir=Path(INDEX_DIR),
    notes_dir=Path(NOTES_DIR),
    life_log_dir=Path(LIFE_LOG_DIR),
    embedding_model_name=EMBEDDING_MODEL,
    llm_model=LLM_MODEL,
    num_research_chunks=NUM_RESEARCH_CHUNKS,
)

@app.on_event("startup")
async def startup_event():
    """On startup, load the agent's knowledge base and start its life cycle."""
    agent.start_life_cycle_task()

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main HTML monitoring page."""
    index_path = static_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="index.html not found")
    return index_path.read_text()


@app.get("/status")
def get_status():
    """Returns the current status of the agent."""
    return {"status": agent.status, "name": agent.name}


@app.get("/notes")
def get_notes():
    """Returns a list of all generated notes."""
    if not agent.notes_dir.exists():
        return []
    
    notes = sorted(
        [f.name for f in agent.notes_dir.glob("*.md")],
        reverse=True
    )
    return notes


@app.get("/notes/{note_filename}")
def get_note(note_filename: str):
    """Returns the content of a specific note."""
    # Basic security: ensure filename is just a filename
    if "/" in note_filename or "\\" in note_filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    note_path = agent.notes_dir / note_filename
    if not note_path.is_file():
        raise HTTPException(status_code=404, detail="Note not found.")
    
    return {"filename": note_filename, "content": note_path.read_text()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
