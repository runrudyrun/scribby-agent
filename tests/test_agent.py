import asyncio
import pytest
import os
from scribby_pi.agent import ScribbyAgent
from scribby_pi import config

@pytest.mark.asyncio
async def test_agent_full_life_cycle_tick():
    """Tests that the agent can complete one full life cycle tick and create a note."""
    # Ensure the notes directory exists
    config.NOTES_DIR.mkdir(exist_ok=True)

    # 1. Get initial state
    notes_before = set(os.listdir(config.NOTES_DIR))

    # 2. Run the agent for one cycle
    agent = ScribbyAgent()
    agent.start()
    assert agent.is_alive

    # Allow the agent to run for one full tick. LLM calls can be slow.
    # The loop itself has a 5s sleep, so we need more than that. LLM calls can be slow.
    await asyncio.sleep(60)

    agent.stop()
    assert not agent.is_alive

    # 3. Check for new note file
    notes_after = set(os.listdir(config.NOTES_DIR))
    new_notes = notes_after - notes_before

    # 4. If the test fails, print the life log for debugging
    if len(new_notes) != 1:
        log_file = config.LOG_DIR / f"life_log_{agent.session_id}.jsonl"
        if log_file.exists():
            print(f"\n--- Agent Life Log ({log_file}) ---")
            with open(log_file, 'r') as f:
                for line in f:
                    print(line.strip())
            print("--- End of Log ---")

    assert len(new_notes) == 1, "A new note file should have been created"

    # 5. Clean up the created note (commented out to inspect the file)
    # if new_notes:
    #     new_note_path = config.NOTES_DIR / new_notes.pop()
    #     if os.path.exists(new_note_path):
    #         os.remove(new_note_path)
