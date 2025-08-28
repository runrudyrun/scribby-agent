import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging
from pathlib import Path
import random

# Silence noisy chromadb logs
logging.getLogger('chromadb').setLevel(logging.CRITICAL)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KnowledgeBase:
    """Manages the agent's knowledge base using ChromaDB."""

    def __init__(self, corpus_dir: Path, index_dir: Path, embedding_model_name: str):
        self.corpus_dir = corpus_dir
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.index_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name, device="cpu"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="scribby_corpus",
            embedding_function=embedding_func
        )
        logging.info(f"ChromaDB collection '{self.collection.name}' loaded/created.")

    def _load_documents(self):
        """Loads all .txt and .md documents from the corpus directory."""
        logging.info(f"Loading documents from {self.corpus_dir}...")
        docs = []
        for file_path in self.corpus_dir.glob("**/*"):
            if file_path.is_file() and file_path.suffix in ['.txt', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        docs.append({'path': str(file_path.relative_to(self.corpus_dir)), 'content': f.read()})
                except Exception as e:
                    logging.error(f"Failed to read {file_path}: {e}")
        logging.info(f"Loaded {len(docs)} documents.")
        return docs

    def _chunk_documents(self, docs: list[dict], chunk_size=512, overlap=50):
        """Splits documents into smaller chunks with metadata and IDs."""
        logging.info("Chunking documents...")
        chunks, metadatas, ids = [], [], []
        chunk_count = 0
        for doc_idx, doc in enumerate(docs):
            content = doc['content']
            for i in range(0, len(content), chunk_size - overlap):
                chunk_text = content[i:i + chunk_size]
                chunks.append(chunk_text)
                metadatas.append({'source': doc['path']})
                ids.append(f"doc{doc_idx}_chunk{chunk_count}")
                chunk_count += 1
        logging.info(f"Created {len(chunks)} chunks.")
        return chunks, metadatas, ids

    def build_index(self):
        """Builds or updates the ChromaDB index from the documents in the corpus."""
        logging.info("Checking for documents to add to the index...")
        docs = self._load_documents()
        if not docs:
            logging.warning("No documents found in corpus. Index will not be updated.")
            return

        chunks, metadatas, ids = self._chunk_documents(docs)
        
        # Simple check to avoid re-indexing identical content.
        # A more robust solution would involve checksums or versioning.
        if self.collection.count() == len(ids):
            logging.info("Index appears to be up-to-date. Skipping build.")
            return

        logging.info(f"Building index with {len(chunks)} chunks...")
        # Clear old collection to rebuild from scratch
        if self.collection.count() > 0:
            logging.info("Clearing existing collection before rebuild.")
            self.client.delete_collection(name=self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                embedding_function=self.collection._embedding_function
            )

        # ChromaDB handles batching internally, but for very large datasets,
        # manual batching might be necessary.
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        logging.info("Index build complete.")

    def search(self, query: str, k: int = 3):
        """Searches the index for the most relevant document chunks."""
        if self.collection.count() == 0:
            logging.error("Index is empty. Cannot perform search.")
            return []
            
        logging.info(f"Searching for query: '{query}'")
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        documents = results.get('documents', [[]])[0]
        logging.info(f"Found {len(documents)} relevant chunks.")
        return documents

    def get_random_chunk(self) -> str | None:
        """Returns a random chunk from the knowledge base."""
        count = self.collection.count()
        if count == 0:
            logging.warning("No document chunks loaded. Cannot get a random chunk.")
            return None
        
        random_offset = random.randint(0, count - 1)
        result = self.collection.get(limit=1, offset=random_offset)
        return result['documents'][0] if result['documents'] else None
