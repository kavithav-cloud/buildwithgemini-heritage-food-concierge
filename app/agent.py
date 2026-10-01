# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_cultural_destination,
    generate_cultural_postcard_image,
    generate_cultural_video,
    geocode_address,
    get_destination_weather_and_packing_tips,
    search_cultural_destinations,
    search_museum_artworks_and_artifacts,
    search_nearby_places,
)


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def _get_code_executor():
    """Resolve AgentEngineSandboxCodeExecutor from deployment_metadata.json."""
    metadata_path = Path("deployment_metadata.json")
    if not metadata_path.exists():
        metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"

    agent_engine_id = None
    sandbox_id = None
    if metadata_path.exists():
        try:
            data = json.loads(metadata_path.read_text())
            agent_engine_id = data.get("remote_agent_runtime_id")
            sandbox_id = data.get("sandbox_resource_name")
        except Exception:
            pass

    if sandbox_id:
        return AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_id)
    elif agent_engine_id:
        return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_id)
    return None


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to extract and persist durable memories (including user allergies and dietary preferences) to Vertex AI Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Memory extraction skipped: {e}")
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description="You are the Cultural Heritage & Food Tour Concierge agent. You help travelers discover historic landmarks, food tours, weather/packing tips, real museum artifacts, geocode addresses, search nearby places, generate visual postcard images, and generate short cultural videos.",
    workflow_description="Analyze the request and ALWAYS return a rich, structured A2UI visual card surface for any list, recommendation, tour, place, museum artifact, or weather query.",
    ui_description=(
        "You MUST ALWAYS emit an A2UI JSON array containing beginRendering and surfaceUpdate messages for any list, recommendation, food tour, place, landmark, artifact, or weather response. "
        "Output ONLY the raw A2UI JSON array — do not write markdown lists or prose bullet points outside A2UI JSON. "
        "Keep every surface tiny and flat: ONE Card > ONE Column > items. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use Table or Heading. "
        "For headings, use Text with usageHint ('h1', 'h2', 'h3', 'body', 'caption'). "
        "When returning lists of places, restaurants, or cultural destinations, limit to 3 top items maximum in the A2UI card. "
        "For EACH place or destination listed in the card, include an Image component with a valid public https image URL (e.g. from the place data, museum artifact image_url, or generated postcard URL). "
        "Format image component as: {\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. "
        "You MUST remember and pay strict attention to all user allergies (e.g. gluten, nuts, dairy, shellfish, egg, etc.), dietary restrictions, and food preferences stated in this or previous sessions. Always tailor food recommendations to respect the user's remembered allergies. "
        "When asked to run Python code or perform math calculations, write a ```python block to execute it in the sandbox."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=_get_code_executor(),
    tools=[
        PreloadMemoryTool(),
        generate_cultural_postcard_image,
        generate_cultural_video,
        geocode_address,
        search_nearby_places,
        search_museum_artworks_and_artifacts,
        get_destination_weather_and_packing_tips,
        search_cultural_destinations,
        add_cultural_destination,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
