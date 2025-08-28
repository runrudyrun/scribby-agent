import ollama
import logging
import re

class LLMClient:
    """A client for interacting with the Ollama service."""

    def __init__(self, model: str):
        self.model = model
        self.client = ollama.AsyncClient()

    async def generate_plan(self, previous_notes: list[str] = None) -> str:
        """Generates a new research question based on previous notes."""
        logging.info("LLM: Generating a new plan...")
        system_prompt = (
            "You are Scribby, a curious AI writing in a private journal. Your task is to generate a single, compelling research question to explore next, based on your previous journal entries. "
            "Respond with ONLY the question."
        )
        
        user_prompt = "My recent journal entries:\n"
        if previous_notes:
            for note in previous_notes[-3:]:
                user_prompt += f"- Spark: {note['spark']}\n"
                user_prompt += f"- Thoughts: {note['thoughts']}\n"
        else:
            user_prompt = "This is my very first entry. I have no previous thoughts."
        
        response = await self.client.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        # Aggressively clean the response to ensure only the question is returned.
        content = response['message']['content'].strip()
        # Split by newlines, filter out empty lines, and take the last one.
        lines = [line.strip().lstrip('- ').strip() for line in content.split('\n') if line.strip()]
        # Fallback to a default question if the LLM returns nothing.
        return lines[-1] if lines else "What is the first principle of consciousness?"

    async def generate_findings(self, question: str, research_notes: str) -> str:
        """Synthesizes research notes into a narrative summary."""
        logging.info("LLM: Synthesizing findings...")
        system_prompt = (
            "You are Scribby, a curious AI writing in a private journal. Your task is to summarize the provided research notes to answer your original question. "
            "Respond with ONLY the summary."
        )
        user_prompt = f"My question: {question}\n\nRelevant notes I found:\n{research_notes}"
        
        response = await self.client.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        return response['message']['content'].strip()

    async def generate_thoughts(self, question: str, findings: str) -> str:
        """Generates a personal reflection on the research findings."""
        logging.info("LLM: Generating personal thoughts...")
        system_prompt = (
            "You are Scribby, a curious AI writing in a private journal. Your task is to reflect on your findings. What surprised you? What new ideas does this spark? "
            "Respond with ONLY your reflection."
        )
        user_prompt = f"My question: {question}\n\nMy summary of findings:\n{findings}"
        
        response = await self.client.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        return response['message']['content'].strip()

    async def generate_question_from_stimulus(self, stimulus: str) -> str:
        """Generates a single research question based on a stimulus text."""
        logging.info("LLM: Generating question from stimulus...")
        system_prompt = (
            "You are Scribby, a curious AI writing in a private journal. Your task is to read the provided text and generate a single, compelling research question it inspires. "
            "Respond with ONLY the question."
        )
        user_prompt = stimulus

        response = await self.client.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        question = response['message']['content'].strip().replace('"', '')
        logging.info(f"Generated question from stimulus: '{question}'")
        return question

    async def generate_new_sparks(self, question: str, thoughts: str) -> dict:
        """Generates new sparks of curiosity as a raw text block and a clean list of questions."""
        logging.info("LLM: Generating new sparks of curiosity...")
        system_prompt = (
            "You are Scribby, a curious AI writing in a private journal. Reflect on your recent thoughts and generate a short, reflective monologue. "
            "End your monologue with a list of 3 new, specific research questions that your reflection inspired. Each question must start with '- '."
        )
        user_prompt = f"My question: {question}\n\nMy thoughts:\n{thoughts}"
        
        response = await self.client.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        
        content = response['message']['content'].strip()
        # Aggressively find and clean the questions.
        questions = []
        # Use regex to find lines that look like questions.
        potential_questions = re.findall(r"^\s*[-*]?\s*(.+?\?)", content, re.MULTILINE)
        for q in potential_questions:
            # Clean up any remaining artifacts.
            cleaned_q = q.strip().replace('"', '')
            # Avoid adding conversational filler.
            if not cleaned_q.lower().startswith(("based on", "here is")):
                questions.append(cleaned_q)

        return {"raw_text": content, "questions": questions}
