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
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from google.genai.types import Content, Part
# --- Local model ---
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool


# these tools work for US only
#from .tools.weather_tools import get_live_weather_forecast
#live_weather_forecast_tool = FunctionTool(func=get_live_weather_forecast)

from .tools.weather_tools_v2 import (
    get_geocoding,
    find_current_weather,
    convert_c2f,
    convert_f2c,
)
geocoding_tool = FunctionTool(func=get_geocoding)
current_weather_tool = FunctionTool(func=find_current_weather)
celsius2fahrenheit_tool = FunctionTool(func=convert_c2f)
fahrenheit2celsius_tool = FunctionTool(func=convert_f2c)


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


#-----------------
# agents
#-----------------
weather_agent = Agent(
    name="weather_agent",
    model=LiteLlm(
        model=f"ollama_chat/{MODEL}",
        api_base=OLLAMA_API_BASE, # Ensure the agent actually points to your env var base!
        think=MODEL_THINKING
    ),
    description="A trip planner that checks the real-time weather before making suggestions.",
    instruction="You are a cautious trip planner. Before suggesting any outdoor activities, you MUST use the `get_live_weather_forecast` tool to check conditions. Incorporate the live weather details into your recommendation.",
    #tools=[live_weather_forecast_tool],
    tools=[geocoding_tool, find_current_weather, convert_f2c, convert_c2f],
)

root_agent = weather_agent
