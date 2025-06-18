"""Host Agent implementation using ADK with a generic A2A delegation tool."""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from config import GOOGLE_API_KEY
from host_agent.prompt import host_agent_instruction_prompt
from host_agent.tools import delegate_task_sync

def create_host_agent() -> Agent:
    """Creates an ADK agent that orchestrates child agents via a generic delegation tool.

    It can coordinate complex workflows by sending detailed instructions to the appropriate child agent.

    Returns:
        Agent: An ADK Agent configured with the generic delegation tool and an orchestration prompt.
    """
    return Agent(
        name="Financial_Researcher_Agent",
        model="gemini-2.0-flash",
        description="A master orchestrator that delegates tasks to specialized child agents (SEC Agent) using a generic A2A communication tool.",
        instruction=host_agent_instruction_prompt,
        tools=[
            delegate_task_sync,
        ],
    )
    
    
root_agent = create_host_agent()