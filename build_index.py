from pathlib import Path
from scribby_pi.knowledge import KnowledgeBase
from scribby_pi.config import (CORPUS_DIR, INDEX_DIR, EMBEDDING_MODEL)

def main():
    print("Building knowledge base index...")

    kb = KnowledgeBase(
        corpus_dir=Path(CORPUS_DIR),
        index_dir=Path(INDEX_DIR),
        embedding_model_name=EMBEDDING_MODEL
    )
    kb.build_index()
    print("Index built successfully.")

if __name__ == "__main__":
    main()
