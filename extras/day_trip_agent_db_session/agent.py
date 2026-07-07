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
from google.adk.sessions import DatabaseSessionService, Session   # <-- swapped import
from google.genai import types
from google.genai.types import Content, Part

MODEL = "gemini-2.5-flash"

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
    tools=[GoogleSearchTool()],
)

root_agent = day_trip_agent

#-----------------
# session service + runner
#-----------------

# SQLite (file-based, zero setup) — good for local dev / testing
DB_URL = "sqlite+aiosqlite:///./adk_sessions.db"

# Or Postgres, e.g.:
# DB_URL = "postgresql+psycopg2://user:password@host:5432/dbname"

session_service = DatabaseSessionService(db_url=DB_URL)

APP_NAME = "day_trip_app"
USER_ID = "user_123"

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

async def main():
    # create_session is async and persists a row in your DB
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        # session_id=... optional, will be generated if omitted
    )


if __name__ == "__main__":
    asyncio.run(main())
