import logging
import os
from unittest import runner

import click
import uvicorn

# A2A server imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

# ADK imports
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService


from sec_agent.agent import create_sec_agent

# Local agent imports
from sec_agent.agent_executor import SecADKAgentExecutor

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_SEC_HOST", "localhost"),
    show_default=True,
    help="Host for the SEC agent server.",
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_SEC_PORT", 8002)),
    show_default=True,
    type=int,
    help="Port for the SEC agent server.",
)
def main(host: str, port: int) -> None:
    
    # Define AgentCard for SEC
    sec_skill = AgentSkill(
        id="sec_search",
        name="Search SEC Filing",
        description="Searches and retrieves information from SEC filings by making API calls to SEC_EDGAR API.",
        tags=["SEC", "search", "retrieval", "knowledge", "company", "filings"],
        examples=[
            "Search for 'Nvidia' cik number",
            "Get Q3 revenue reported by Nvidia in 2023"
        ],
    )
    
    agent_card = AgentCard(
        name="SEC Filings Search Agent",
        description="Provides information retrieval services from United States Securities and Exchange Commissions API using MCP.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        skills=[sec_skill],
    )
    
    try:
        agent = create_sec_agent()
    
        runner = Runner(
            agent=agent,
            app_name=agent_card.name,
            
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService()
        )
        
        agent_executor = SecADKAgentExecutor(
            agent=agent,
            agent_card=agent_card,
            runner=runner
        )    
        
    except Exception as e:
        logger.error(f"Failed to initialize SEC Agent components: {e}", exc_info=True)
        return
    
    # Set up the A2A request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )
    
    # Create the A2A Starlette application
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    
    logger.info(f"Starting SEC Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f"  Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    # Run the Uvicorn server
    uvicorn.run(a2a_app.build(), host=host, port=port)

if __name__ == "__main__":
    main()
    
    
