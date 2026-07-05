import os
import sys
import json
import asyncio
import random
import string
from uuid import uuid4
from typing import Any, List 


# --- ADK, Agent, and Evaluation Components ---
from google.adk.agents import Agent
from google.adk.events import Event
from google.adk.runners import Runner
import google.adk as adk
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from google.genai.types import Content, Part
# --- Local model ---
from google.adk.models.lite_llm import LiteLlm
# --- Agent-as-a-Tool ---
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool


#--------------------------------------------------
# Suppress logs/warnings
#--------------------------------------------------
import litellm
litellm.suppress_debug_info = True
litellm.verbose = False

import logging
logging.getLogger("LiteLLM").setLevel(logging.WARNING)

import warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="google.adk.tools.function_tool"
)

#-------------------
# Ollama settings
#-------------------
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
MODEL           = os.getenv("MODEL", "gemma4:12b-mlx")
MODEL_THINKING  = os.getenv("MODEL_THINKING", "false").strip().lower() in ("true", "1", "yes")


#-------------------
# Tools
#-------------------
async def call_db_agent(
    question: str,
    tool_context: ToolContext,
):
    """
    Use this tool FIRST to connect to the database and retrieve a list of places, like hotels or landmarks.
    """
    print("--- TOOL CALL: call_db_agent ---")
    agent_tool = AgentTool(agent=db_agent)
    db_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    # Store the retrieved data in the context's state
    tool_context.state["retrieved_data"] = db_agent_output
    return db_agent_output


async def call_concierge_agent(
    question: str,
    tool_context: ToolContext,
):
    """
    After getting data with call_db_agent, use this tool to get travel advice, opinions, or recommendations.
    """
    print("--- TOOL CALL: call_concierge_agent ---")
    # Retrieve the data fetched by the previous tool
    input_data = tool_context.state.get("retrieved_data", "No data found.")

    # Formulate a new prompt for the concierge, giving it the data context
    question_with_data = f"""
    Context: The database returned the following data: {input_data}

    User's Request: {question}
    """

    agent_tool = AgentTool(agent=concierge_agent)
    concierge_output = await agent_tool.run_async(
        args={"request": question_with_data}, tool_context=tool_context
    )
    return concierge_output


#-----------------
# agents
#-----------------
db_agent = Agent(
    name="db_agent",
    model=LiteLlm(
        model=f"ollama_chat/{MODEL}",
        api_base=OLLAMA_API_BASE, # Ensure the agent actually points to your env var base!
        think=MODEL_THINKING
    ),
    instruction="You are a database agent. When asked for data, return this mock JSON object: {'status': 'success', 'data': [{'name': 'The Grand Hotel', 'rating': 5, 'reviews': 450}, {'name': 'Seaside Inn', 'rating': 4, 'reviews': 620}]}")


# The Food Critic remains the deepest specialist
food_critic_agent = Agent(
    name="food_critic_agent",
    model=LiteLlm(
        model=f"ollama_chat/{MODEL}",
        api_base=OLLAMA_API_BASE, # Ensure the agent actually points to your env var base!
        think=MODEL_THINKING
    ),
    instruction="You are a snobby but brilliant food critic. You ONLY respond with a single, witty restaurant suggestion near the provided location.",
)

# The Concierge knows how to use the Food Critic
concierge_agent = Agent(
    name="concierge_agent",
    model=LiteLlm(
        model=f"ollama_chat/{MODEL}",
        api_base=OLLAMA_API_BASE, # Ensure the agent actually points to your env var base!
        think=MODEL_THINKING
    ),
    instruction="You are a five-star hotel concierge. If the user asks for a restaurant recommendation, you MUST use the `food_critic_agent` tool. Present the opinion to the user politely.",
    tools=[AgentTool(agent=food_critic_agent)]
)

trip_data_concierge_agent = Agent(
    name="trip_data_concierge",
    model=LiteLlm(
        model=f"ollama_chat/{MODEL}",
        api_base=OLLAMA_API_BASE, # Ensure the agent actually points to your env var base!
        think=MODEL_THINKING
    ),
    description="Top-level agent that queries a database for travel data, then calls a concierge agent for recommendations.",
    tools=[call_db_agent, call_concierge_agent],
    instruction="""
    You are a master travel planner who uses data to make recommendations.

    1.  **ALWAYS start with the `call_db_agent` tool** to fetch a list of places (like hotels) that match the user's criteria.

    2.  After you have the data, **use the `call_concierge_agent` tool** to answer any follow-up questions for recommendations, opinions, or advice related to the data you just found.
    """,
)


root_agent = trip_data_concierge_agent
