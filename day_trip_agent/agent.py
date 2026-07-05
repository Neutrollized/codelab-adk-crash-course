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
    tools=[GoogleSearchTool()],
)

root_agent = day_trip_agent
