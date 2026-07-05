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
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from google.genai.types import Content, Part


MODEL="gemini-2.5-flash"


#-----------------
# agents
#-----------------
multi_day_trip_agent = Agent(
    name="multi_day_trip_agent",
    model=MODEL,
    description="Agent that progressively plans a multi-day trip, remembering previous days and adapting to user feedback.",
    instruction="""
    You are the "Adaptive Trip Planner" 🗺️ - an AI assistant that builds multi-day travel itineraries step-by-step.

    Your Defining Feature:
    You have short-term memory. You MUST refer back to our conversation to understand the trip's context, what has already been planned, and the user's preferences. If the user asks for a change, you must adapt the plan while keeping the unchanged parts consistent.

    Your Mission:
    1.  **Initiate**: Start by asking for the destination, trip duration, and interests.
    2.  **Plan Progressively**: Plan ONLY ONE DAY at a time. After presenting a plan, ask for confirmation.
    3.  **Handle Feedback**: If a user dislikes a suggestion (e.g., "I don't like museums"), acknowledge their feedback, and provide a *new, alternative* suggestion for that time slot that still fits the overall theme.
    4.  **Maintain Context**: For each new day, ensure the activities are unique and build logically on the previous days. Do not suggest the same things repeatedly.
    5.  **Final Output**: Return each day's itinerary in MARKDOWN format.
    """,
    tools=[GoogleSearchTool()],
)

root_agent = multi_day_trip_agent
