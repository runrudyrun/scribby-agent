import asyncio
import signal
import logging
from scribby_pi.agent import ScribbyAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """Main function to run the agent."""
    agent = ScribbyAgent()

    def signal_handler():
        logging.info("Shutdown signal received. Halting agent...")
        agent.stop()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    agent.start()

    # Keep the main function running until the agent is stopped
    try:
        if agent.life_cycle_task:
            await agent.life_cycle_task
    except asyncio.CancelledError:
        pass # Expected on shutdown

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application shut down.")
