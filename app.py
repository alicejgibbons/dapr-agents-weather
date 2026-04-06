#
# Copyright 2026 The Dapr Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import logging
from typing import Optional

import chainlit as cl

from dapr_agents import DurableAgent, AgentRunner
from dapr_agents.agents.configs import AgentMemoryConfig, AgentStateConfig
from dapr_agents.llm import DaprChatClient
from dapr_agents.memory import ConversationDaprStateMemory
from dapr_agents.storage.daprstores.stateservice import StateStoreService
from dapr_agents.tool.mcp.client import MCPClient

logger = logging.getLogger(__name__)

_agent: Optional[DurableAgent] = None
_runner: Optional[AgentRunner] = None
_initialized = False


def _extract_content(result: str | None) -> str:
    """Extract the content field from a serialized workflow result."""
    if not result:
        return ""
    try:
        parsed = json.loads(result)
        return parsed.get("content", result)
    except (json.JSONDecodeError, AttributeError):
        return result


async def _ensure_initialized() -> tuple[DurableAgent, AgentRunner]:
    """Initialize the agent, runner, and MCP clients exactly once."""
    global _agent, _runner, _initialized

    if _initialized:
        return _agent, _runner

    mcp_client = MCPClient()

    await mcp_client.connect_streamable_http(
        server_name="mongodb",
        url="http://localhost:3000/mcp",
    )
    logger.info("Connected to MongoDB MCP server (%d tools loaded)", len(mcp_client.get_server_tools("mongodb")))

    await mcp_client.connect_stdio(
        server_name="weather",
        command="npx",
        args=["-y", "-p", "open-meteo-mcp-server", "open-meteo-mcp-server"],
    )
    logger.info("Connected to Open-Meteo MCP server (%d tools loaded)", len(mcp_client.get_server_tools("weather")))

    _agent = DurableAgent(
        name="WeatherAgent",
        role="Weather Assistant",
        instructions=[
            "Help users with weather information.",
            "Always follow this two-step process:",
            "Step 1 — look up the city in MongoDB using the database 'weatherdb', "
            "collection 'cities'. Each document has: name (string), country (string), "
            "latitude (float), longitude (float). Query by the 'name' field. "
            "If the city is not found, tell the user and stop.",
            "Step 2 — use the Open-Meteo weather_forecast tool with the latitude and "
            "longitude from the MongoDB result to get the current weather. "
            "Request the 'temperature_2m' hourly variable and use the most recent value.",
            "Return the city name, country, coordinates, and current temperature in your answer.",
        ],
        tools=mcp_client.get_all_tools(),
        llm=DaprChatClient(component_name="llm-provider"),
        memory=AgentMemoryConfig(
            store=ConversationDaprStateMemory(store_name="agent-memory"),
        ),
        state=AgentStateConfig(
            store=StateStoreService(store_name="agent-workflow"),
        ),
    )

    _runner = AgentRunner()
    _runner.workflow(_agent)

    _initialized = True
    return _agent, _runner


@cl.on_chat_start
async def on_chat_start():
    await _ensure_initialized()
    await cl.Message(content="Weather agent ready. Ask me about the weather in any city!").send()


@cl.on_chat_end
async def on_chat_end():
    pass


@cl.on_message
async def on_message(message: cl.Message):
    agent, runner = await _ensure_initialized()
    try:
        result = await runner.run(agent, {"task": message.content})
        await cl.Message(content=_extract_content(result)).send()
    except Exception as exc:
        await cl.Message(content=f"Sorry, something went wrong: {exc}").send()
