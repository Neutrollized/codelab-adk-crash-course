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
day_trip_agent = Agent(
    name="day_trip_agent",
    model=MODEL,
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
    model=MODEL,
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
    model=MODEL,
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


# --- iteratgive planner agent ---
planner_agent = Agent(
    name="planner_agent",
    model=MODEL,
    tools=[GoogleSearchTool()],
    instruction="You are a trip planner. Based on the user's request, propose a single activity and a single restaurant. Output only the names, like: 'Activity: Exploratorium, Restaurant: La Mar'.",
    output_key="current_plan"
)

critic_agent = Agent(
    name="critic_agent",
    model=MODEL,
    tools=[GoogleSearchTool()],
    instruction=f"""You are a logistics expert. Your job is to critique a travel plan. The user has a strict constraint: total travel time must be short.
    Current Plan: {{current_plan}}
    Use your tools to check the travel time between the two locations.
    IF the travel time is over 45 minutes, provide a critique, like: 'This plan is inefficient. Find a restaurant closer to the activity.'
    ELSE, respond with the exact phrase: '{COMPLETION_PHRASE}'""",
    output_key="criticism"
)

refiner_agent = Agent(
    name="refiner_agent",
    model=MODEL,
    tools=[GoogleSearchTool(bypass_multi_tools_limit=True), exit_loop],
    instruction=f"""You are a trip planner, refining a plan based on criticism.
    Original Request: {{session.query}}
    Critique: {{criticism}}
    IF the critique is '{COMPLETION_PHRASE}', you MUST call the 'exit_loop' tool.
    ELSE, generate a NEW plan that addresses the critique. Output only the new plan names, like: 'Activity: de Young Museum, Restaurant: Nopa'.""",
    output_key="current_plan"
)

refinement_loop = LoopAgent(
    name="refinement_loop",
    sub_agents=[critic_agent, refiner_agent],
    max_iterations=3
)

iterative_planner_agent = SequentialAgent(
    name="iterative_planner_agent",
    sub_agents=[planner_agent, refinement_loop],
    description="A workflow that iteratively plans and refines a trip to meet constraints."
)


# --- parallel planner agent ---
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



# --- The Brain of the Operation: The Router Agent ---
router_agent = Agent(
    name="router_agent",
    model=MODEL,
    instruction="""
    You are a request router. Your job is to analyze a user's query and decide which of the following agents or workflows is best suited to handle it.
    Do not answer the query yourself, use the most appropriate tool available to you.

    Available Options:
    - 'foodie_agent': For queries *only* about food, restaurants, or eating.
    - 'weekend_guide_agent': For queries about events, concerts, or activities happening on a specific timeframe like a weekend.
    - 'day_trip_agent': A general planner for any other day trip requests.
    - 'find_and_navigate_agent': Use this for complex queries that ask to *first find a place* and *then get directions* to it.
    - 'iterative_planner_agent': For planning a trip with a specific constraint that needs checking, like travel time.
    - 'parallel_planner_agent': For queries that ask to find multiple, independent things at once (e.g., a museum AND a concert AND a restaurant).
    """,
    tools=[
        AgentTool(day_trip_agent),
        AgentTool(foodie_agent),
        AgentTool(find_and_navigate_agent),
        AgentTool(iterative_planner_agent),
        AgentTool(parallel_planner_agent)
    ]
)

root_agent = router_agent
