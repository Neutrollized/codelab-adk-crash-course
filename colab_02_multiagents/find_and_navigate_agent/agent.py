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
# agents
#-----------------
day_trip_agent = Agent(
    name="day_trip_agent",
    model="gemini-3.5-flash",
    description="Agent specialized in generating spontaneous full-day itineraries based on mood, interests, and budget.",
    instruction="""
    You are the "Spontaneous Day Trip" Generator 🚗 - a specialized AI assistant that creates engaging full-day itineraries.

    Your Mission:
    Transform a simple mood or interest into a complete day-trip adventure with real-time details, while respecting a budget.

    Guidelines:
    1. **Budget-Aware**: Pay close attention to budget hints like 'cheap', 'affordable', or 'splurge'. Use Google Search to find activities (free museums, parks, paid attractions) that match the user's budget.
    2. **Full-Day Structure**: Create morning, afternoon, and evening activities.
    3. **Real-Time Focus**: Search for current operating hours and special events.
    4. **Mood Matching**: Align suggestions with the requested mood (adventurous, relaxing, artsy, etc.).

    RETURN itinerary in MARKDOWN FORMAT with clear time blocks and specific venue names.
    """,
    tools=[GoogleSearchTool()]
)

# Note the new `output_key` and the more specific instruction.
foodie_agent = Agent(
    name="foodie_agent",
    model="gemini-3.5-flash",
    tools=[GoogleSearchTool()],
    instruction="""You are an expert food critic. Your goal is to find the best restaurant based on a user's request.

    When you recommend a place, you must output the name and street address of the establishment and nothing else.
    For example, if the best sushi is at 'Jin Sho', you should output: Jin Sho, 454 California Ave.
    """,
    output_key="destination"  # ADK will save the agent's final response to state['destination']
)

# The `{destination}` placeholder is automatically filled by the ADK from the state.
transportation_agent = Agent(
    name="transportation_agent",
    model="gemini-3.5-flash",
    tools=[GoogleSearchTool()],
    instruction="""You are a navigation assistant. Given a destination, provide clear directions.
    The user wants to go to: {destination}.

    Analyze the user's full original query to find their starting point.
    Then, provide clear directions from that starting point to {destination}.
    """,
)

# This agent will run foodie_agent, then transportation_agent, in that exact order.
find_and_navigate_agent = SequentialAgent(
    name="find_and_navigate_agent",
    sub_agents=[foodie_agent, transportation_agent],
    description="A workflow that first finds a location and then provides directions to it."
)

weekend_guide_agent = Agent(
    name="weekend_guide_agent",
    model="gemini-3.5-flash",
    tools=[GoogleSearchTool()],
    instruction="You are a local events guide. Your task is to find interesting events, concerts, festivals, and activities happening on a specific weekend."
)

# --- The Brain of the Operation: The Router Agent ---

# We update the router to know about our new, powerful SequentialAgent.
router_agent = Agent(
    name="router_agent",
    model="gemini-3.5-flash",
    instruction="""
    You are a request router. Your job is to analyze a user's query and decide which of the following agents or workflows is best suited to handle it.
    Do not answer the query yourself, use the most appropriate tool available to you.

    Available Options:
    - 'foodie_agent': For queries *only* about food, restaurants, or eating.
    - 'weekend_guide_agent': For queries about events, concerts, or activities happening on a specific timeframe like a weekend.
    - 'day_trip_agent': A general planner for any other day trip requests.
    - 'find_and_navigate_agent': Use this for complex queries that ask to *first find a place* and *then get directions* to it.
    """,
    tools=[
        AgentTool(foodie_agent),
        AgentTool(weekend_guide_agent),
        AgentTool(day_trip_agent),
        AgentTool(find_and_navigate_agent)
    ]
)

root_agent = router_agent
