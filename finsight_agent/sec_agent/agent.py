import json
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm
from utils.custom_adk_patches import CustomMCPToolset

from config import GOOGLE_API_KEY
from sec_agent.prompt import sec_agent_instruction_prompt



def create_sec_agent() -> Agent:
    return Agent(
        name="sec_filings_mcp_agent",
        model="gemini-2.0-flash",
        description="Specialized agent for retrieving information from Notion workspace via MCPToolset.",
        instruction=sec_agent_instruction_prompt,
        tools=[
            CustomMCPToolset(
                connection_params=StdioServerParameters(
                    command='python',
                    args=['/Users/rohituddagiri/Documents/Python Scripts/AI Projects/FinSight/FinSight/mcp_server/sec_edgar_server/main.py'] 
                )
            )
        ]
    )
    
    

root_agent = create_sec_agent()