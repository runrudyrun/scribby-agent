# Scribby-Pi

A cozy, offline-first AI agent that "lives" by performing research cycles on a local corpus of documents.

## Project Goal

Scribby-Pi is a simulation of a living companion agent. Its life is a continuous cycle of curiosity: reading from a local corpus, writing notes, reflecting on its findings, and planning its next questions. Over time, its notes become a unique "life diary." The agent is designed to run entirely offline on devices such as Raspberry Pi 4/5, using small, local language models.

## Architecture

The agent operates on a simple, robust loop and can be monitored via a local web interface.

### Core Agent (Raspberry Pi)

- **Orchestrator**: Manages the life cycle of the agent via a FastAPI web server.
- **Small LLM**: Uses a GGUF-quantized model (e.g., `phi3:mini`) via `ollama` for generation tasks.
- **Local Embeddings**: Employs a lightweight model (`all-MiniLM-L6-v2`) for retrieval tasks.
- **Vector Store**: Uses **ChromaDB** for efficient, persistent similarity search on the local corpus.
- **Data Storage**: All persistent data is stored locally in the `/data` directory:
    - `/data/corpus`: The source documents for the agent's knowledge.
    - `/data/notes`: The agent's generated "life diary."
    - `/data/index`: The ChromaDB persistent index.
    - `/data/life_log`: Chronological logs of the agent's cycles.

### The Life Cycle

The agent's existence is defined by a continuous, four-stage loop:

1.  **Planner**: The agent reflects on its previous findings and decides on a new research question.
2.  **Researcher**: It converts the question into an embedding and performs a similarity search (RAG) against the local corpus index to find relevant information.
3.  **Writer**: It synthesizes the retrieved information into a coherent note, which is saved to its diary.
4.  **Critic**: The agent reflects on the newly written note, evaluates its own work, and identifies open questions, which feeds back into the planning stage.

This loop is the agent's "life." If it stops, the agent's life ends.

## Getting Started

The recommended way to run Scribby-Pi is using Docker, especially on a Raspberry Pi.

### Prerequisites

- Docker installed.
- On the host machine, `ollama` should be installed and running with a small model available (e.g., `ollama pull phi3:mini`).

### Deployment with Docker (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd scribby-pi
    ```

2.  **Add Corpus Files**:
    Place your `.txt` or `.md` files into the `data/corpus` directory.

3.  **Build the Docker Image**:
    This command builds the image and pre-builds the knowledge base index, which may take some time.
    ```bash
    docker build -t scribby-pi .
    ```

4.  **Run the Container**:
    This command runs the agent. Note that `--network=host` is used to allow the container to access the `ollama` service running on the host machine.
    ```bash
    docker run -d --name scribby-agent -v ./data:/app/data --network=host scribby-pi
    ```

5.  **Monitor the Agent**:
    Open your browser and navigate to `http://localhost:8000` to see the agent's status and notes.

### Local Development (Without Docker)

1.  **Install Dependencies**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Build the Index**:
    ```bash
    python3 build_index.py
    ```

3.  **Run the Server**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
