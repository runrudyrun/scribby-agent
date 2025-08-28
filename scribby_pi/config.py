from pathlib import Path

# Base data directory
DATA_DIR = Path("data")

# Subdirectories
CORPUS_DIR = DATA_DIR / "corpus"
NOTES_DIR = DATA_DIR / "notes"
INDEX_DIR = DATA_DIR / "index"
LOG_DIR = DATA_DIR / "life_log"

# Ensure directories exist
for path in [DATA_DIR, CORPUS_DIR, NOTES_DIR, INDEX_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Simulation parameters
AGENT_NAME = "Scribby"
LLM_MODEL = "phi3:mini"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
NUM_RESEARCH_CHUNKS = 5
