<!--
Copyright 2026 The Dapr Authors
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Durable Weather Agent

A `DurableAgent` backed by the Dapr Workflow engine with a Chainlit chat UI. Every step of execution is persisted to durable storage, allowing long-running interactions to survive interruptions.

The agent uses two MCP servers:

- **MongoDB MCP** — looks up city metadata (country, coordinates) from a local MongoDB database
- **Open-Meteo MCP** — fetches real current weather using latitude/longitude from the Open-Meteo API (free, no API key required)

For each request the agent first queries MongoDB to confirm the city exists and retrieve its coordinates, then passes those coordinates to the Open-Meteo weather tool, and returns a combined answer.

## Prerequisites

- Python >= 3.11 ([python.org](https://www.python.org/downloads/))
- Node.js >= 20 ([nodejs.org](https://nodejs.org/)) — for the MongoDB MCP server
- Docker ([docs.docker.com](https://docs.docker.com/get-docker/))
- Dapr CLI ([docs.dapr.io](https://docs.dapr.io/getting-started/install-dapr-cli/))
- uv package manager ([docs.astral.sh](https://docs.astral.sh/uv/getting-started/installation/))
- Ollama ([ollama.com](https://ollama.com/)) **or** an OpenAI API key

## Setup

### 1. Install Python dependencies

```bash
uv venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
uv sync
```

### 2. Initialize Dapr

```bash
dapr init
```

### 3. Start MongoDB in Docker

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  mongo:7
```

Verify it is running:

```bash
docker ps | grep mongodb
```

### 4. Seed the city data

```bash
python seed_mongodb.py
```

This script inserts 9 cities (London, New York, Tokyo, Paris, Sydney, São Paulo, Cairo, Mumbai, Seattle) into a `weatherdb.cities` collection. Re-running the script is safe — it drops and recreates the collection each time.

### 5. Start the MongoDB MCP server

The MongoDB MCP server connects to your local MongoDB instance and exposes its tools via streamable HTTP on `http://localhost:3000/mcp`.

```bash
MDB_MCP_CONNECTION_STRING="mongodb://localhost:27017/weatherdb" \
  npx -y mongodb-mcp-server@latest --transport http --httpHost 127.0.0.1 --httpPort 3000
```

Leave this running in a dedicated terminal.

### 6. Install the Open-Meteo MCP server

Launch a new terminal. The Open-Meteo MCP server is launched automatically by the agent via `npx` when it starts. Pre-install it to avoid the download delay at startup:

```bash
npx -y -p open-meteo-mcp-server open-meteo-mcp-server --help
```

### 7. Configure your LLM provider

Set your OPENAI_API_KEY in terminal which will be picked up by the `resources/llm-provider.yaml` component:

```
export OPENAI_API_KEY=""
```


```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: llm-provider
spec:
  type: conversation.openai
  version: v1
  metadata:
    - name: key
      envRef: OPENAI_API_KEY
    - name: model
      value: "gpt-4o-mini"
```

## Run

In a new terminal:

```bash
uv run dapr run --app-id durable-agent --resources-path resources -- chainlit run app.py
```

Then open [http://localhost:8000](http://localhost:8000) in your browser and start chatting.

## Expected Behavior

1. The agent queries MongoDB to look up the city (e.g. London → United Kingdom, 51.51°N, 0.13°W).
2. The agent passes the coordinates to the Open-Meteo weather tool and retrieves the current temperature.
3. The agent returns a combined answer with the city name, country, coordinates, and current weather.

## Troubleshooting

- **MongoDB not reachable**: Ensure `docker ps` shows the `mongodb` container running on port 27017
- **MongoDB MCP not reachable**: Ensure the `npx mongodb-mcp-server` process is running and listening on port 3000
- **City not found**: Only the 8 seeded cities are in the database. Re-run `seed_mongodb.py` if needed
- **Open-Meteo MCP slow to start**: The first run downloads the package via npx. Pre-install it with the command in step 6
- **Ollama not responding**: Ensure `ollama serve` is running and the model is pulled (`ollama pull qwen3:0.6b`)
- **Environment variables**: Verify `OLLAMA_ENDPOINT` and `OLLAMA_MODEL` are exported (or `OPENAI_API_KEY` if using OpenAI)
- **Import errors**: Verify that `uv sync` completed successfully
- **Python version**: Ensure you are using Python >= 3.11
