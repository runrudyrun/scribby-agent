import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from .knowledge import KnowledgeBase
from .llm import LLMClient


class ScribbyAgent:
    """The main agent class for Scribby-Pi."""

    def __init__(
        self,
        name: str,
        corpus_dir: Path,
        index_dir: Path,
        notes_dir: Path,
        life_log_dir: Path,
        embedding_model_name: str,
        llm_model: str,
        num_research_chunks: int,
    ):
        self.name = name
        self.status = "Born"
        self.is_alive = False
        self.life_cycle_task = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Store paths and config
        self.notes_dir = notes_dir
        self.life_log_dir = life_log_dir
        self.num_research_chunks = num_research_chunks

        self._setup_life_logger()

        self.knowledge_base = KnowledgeBase(
            corpus_dir=corpus_dir,
            index_dir=index_dir,
            embedding_model_name=embedding_model_name
        )
        self.llm_client = LLMClient(model=llm_model)
        self.note_history = []
        self.open_questions = []

    def _setup_life_logger(self):
        """Sets up a dedicated logger for life cycle events."""
        self.life_log_dir.mkdir(parents=True, exist_ok=True)
        self.life_logger = logging.getLogger('life_log')
        self.life_logger.setLevel(logging.INFO)
        log_file = self.life_log_dir / f"life_log_{self.session_id}.jsonl"
        handler = logging.FileHandler(log_file)
        self.life_logger.addHandler(handler)
        self.life_logger.propagate = False

    def _log_life_event(self, event_type: str, details: dict):
        """Logs a structured life cycle event to the life log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'event_type': event_type,
            'details': details,
        }
        self.life_logger.info(json.dumps(log_entry))

    async def _planner(self):
        """Plans the next research question."""
        self.status = "Planning"
        logging.info("Planner: Thinking about what to research next...")
        self._log_life_event('PLAN_START', {'open_questions': len(self.open_questions)})
        
        if self.open_questions:
            question = self.open_questions.pop(0)
            logging.info(f"Taking next question from open questions: '{question}'")
        elif not self.note_history:
            logging.info("First run. Generating question from a random knowledge base chunk.")
            stimulus = self.knowledge_base.get_random_chunk()
            if stimulus:
                question = await self.llm_client.generate_question_from_stimulus(stimulus)
            else:
                logging.warning("Knowledge base is empty. Using a default question.")
                question = "What is the nature of consciousness?"
        else:
            question = await self.llm_client.generate_plan(self.note_history)

        self._log_life_event('PLAN_COMPLETE', {'question': question})
        return question

    async def _researcher(self, question: str):
        """Researches a question using the local corpus."""
        self.status = "Researching"
        logging.info(f"Researcher: Researching '{question}'...")
        self._log_life_event('RESEARCH_START', {'question': question})

        results = self.knowledge_base.search(question, self.num_research_chunks)

        if not results:
            notes = "No relevant information found in the knowledge base."
            self._log_life_event('RESEARCH_COMPLETE', {'question': question, 'chunks_found': 0})
        else:
            notes = "\n\n---\n\n".join(results)
            self._log_life_event('RESEARCH_COMPLETE', {'question': question, 'chunks_found': len(results)})
        
        return notes

    async def _write_journal_entry(self, question: str, research_notes: str):
        """Generates a journal entry, saves it, and updates agent memory."""
        self.status = "Writing"
        logging.info("Writer: Reflecting and writing journal entry...")
        self._log_life_event('WRITE_START', {'question': question})

        # 1. Generate each part of the journal entry sequentially.
        findings = await self.llm_client.generate_findings(question, research_notes)
        thoughts = await self.llm_client.generate_thoughts(question, findings)
        sparks_result = await self.llm_client.generate_new_sparks(question, thoughts)
        
        # Check if we got the expected dictionary
        if not isinstance(sparks_result, dict) or "questions" not in sparks_result or "raw_text" not in sparks_result:
            logging.error(f"LLM returned unexpected data for new_sparks: {sparks_result}")
            self._log_life_event('WRITE_FAILED', {'reason': 'Malformed sparks_result from LLM'})
            return

        new_sparks_clean = sparks_result["questions"]
        new_sparks_raw = sparks_result["raw_text"]

        if not all([findings, thoughts]):
            logging.error("LLM failed to generate findings or thoughts. Skipping tick.")
            self._log_life_event('WRITE_FAILED', {'reason': 'Incomplete LLM response for findings/thoughts'})
            return

        # 2. Store structured data for the agent's own use.
        self.note_history.append({
            'spark': question,
            'findings': findings,
            'thoughts': thoughts,
            'new_sparks': new_sparks_clean
        })
        self.open_questions.extend(new_sparks_clean)
        logging.info(f"Writer: Generated {len(new_sparks_clean)} new questions.")

        # 3. Assemble the note for human readability and save it.
        timestamp = datetime.now()
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        note_path = self.notes_dir / f"note_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        content = (
            f"# Journal Entry: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"**Initial Spark:** {question}\n\n"
            f"## Findings\n{findings}\n\n"
            f"## My Thoughts\n{thoughts}\n\n"
            f"## New Sparks\n{new_sparks_raw}"  # Use the raw text for the diary
        )

        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Writer: Note saved to {note_path}")
        self._log_life_event('WRITE_COMPLETE', {
            'note_path': str(note_path),
            'new_questions_generated': len(new_sparks_clean)
        })

    async def run_life_cycle(self):
        """The main life cycle loop of the agent."""
        tick_count = 0
        while self.is_alive:
            tick_count += 1
            logging.info(f"--- New Life Cycle Tick #{tick_count} ---")
            self._log_life_event('TICK_START', {'tick_id': tick_count})
            
            question = await self._planner()
            research_notes = await self._researcher(question)
            await self._write_journal_entry(question, research_notes)
            
            self._log_life_event('TICK_COMPLETE', {'tick_id': tick_count})
            self.status = "Sleeping"
            await asyncio.sleep(5)

    def load_knowledge_base(self):
        """Builds the initial knowledge base index."""
        logging.info("Preparing knowledge base...")
        self.knowledge_base.build_index()
        logging.info("Knowledge base is ready.")

    def start_life_cycle_task(self):
        """Creates and starts the life cycle asyncio task."""
        if not self.is_alive:
            self.is_alive = True
            self.life_cycle_task = asyncio.create_task(self.run_life_cycle())
            logging.info(f"Agent '{self.name}' has started its life cycle.")

    def stop(self):
        """Stops the agent's life cycle."""
        if self.is_alive:
            self.is_alive = False
            if self.life_cycle_task:
                self.life_cycle_task.cancel()
                self.life_cycle_task = None
            self.status = "Halted"
            logging.info(f"Agent '{self.name}' has been halted.")
