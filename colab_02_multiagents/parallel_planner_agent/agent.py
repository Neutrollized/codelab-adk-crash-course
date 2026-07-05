import os
import sys
import json
import asyncio
import random
import string
from uuid import uuid4
from typing import Any, List 


# --- ADK, Agent, and Evaluation Components ---
from google.adk.agents import Agent, SequentialAgent, LoopAgent, ParallelAgent
from google.adk.events import Event
from google.adk.runners import Runner
import google.adk as adk
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from google.genai.types import Content, Part


MODEL="gemini-2.5-flash"


#--------------------------------------------------
# Suppress logs/warnings
#--------------------------------------------------
import warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="google.adk.models.llm_request"
)


#-----------------
# tools
#-----------------
# A tool to signal that the loop should terminate
COMPLETION_PHRASE = "The plan is feasible and meets all constraints."
def exit_loop(tool_context: ToolContext):
  """Call this function ONLY when the plan is approved, signaling the loop should end."""
  print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
  tool_context.actions.escalate = True
  return {}


#-----------------
# agents
#-----------------
# Specialist Agent 1
museum_finder_agent = Agent(
    name="museum_finder_agent",
    model=MODEL,
    tools=[GoogleSearchTool()],
    instruction="You are a museum expert. Find the best museum based on the user's query. Output only the museum's name.",
    output_key="museum_result"
)

# Specialist Agent 2
concert_finder_agent = Agent(
    name="concert_finder_agent",
    model=MODEL,
    tools=[GoogleSearchTool()],
    instruction="You are an events guide. Find a concert based on the user's query. Output only the concert name and artist.",
    output_key="concert_result"
)

# We can reuse our foodie_agent for the third parallel task!
# Just need to give it a new output_key for this workflow.
# restaurant_finder_agent = foodie_agent.copy(update={"output_key": "restaurant_result"})
restaurant_finder_agent = Agent(
    name="restaurant_finder_agent",
    model=MODEL,
    tools=[GoogleSearchTool()],
    instruction="""You are an expert food critic. Your goal is to find the best restaurant based on a user's request.

    When you recommend a place, you must output the name and street address of the establishment and nothing else.
    For example, if the best sushi is at 'Jin Sho', you should output: Jin Sho, 454 California Ave.
    """,
    output_key="restaurant_result" # Set the correct output key for this workflow
)


# ✨ The ParallelAgent runs all three specialists at once ✨
parallel_research_agent = ParallelAgent(
    name="parallel_research_agent",
    sub_agents=[museum_finder_agent, concert_finder_agent, restaurant_finder_agent]
)

# Agent to synthesize the parallel results
synthesis_agent = Agent(
    name="synthesis_agent",
    model=MODEL,
    instruction="""You are a helpful assistant. Combine the following research results into a clear, bulleted list for the user.
    - Museum: {museum_result}
    - Concert: {concert_result}
    - Restaurant: {restaurant_result}
    """
)

parallel_planner_agent = SequentialAgent(
    name="parallel_planner_agent",
    sub_agents=[parallel_research_agent, synthesis_agent],
    description="A workflow that finds multiple things in parallel and then summarizes the results."
)


root_agent = parallel_planner_agent
