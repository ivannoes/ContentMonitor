# ContentMonitor

An AI-powered tool that monitors RSS feeds and performs Google searches to detect content based on configurable keywords. It uses an **OpenAI model** with **function calling** (Responses API) to intelligently collect, filter, and summarize results.

Originally designed for anti-piracy research, it can be adapted for any topic monitoring.

## Architecture

```
content_monitor.py   ← Entry point: builds prompt & runs the agent
agent.py             ← OpenAI Responses API function-calling loop
config.py            ← Centralised configuration (env vars, keywords)
tools/
  __init__.py        ← Tool registry (add new tools here)
  base.py            ← Abstract BaseTool class
  google_search.py   ← Google Custom Search tool
  feed_reader.py     ← RSS / Atom feed reader tool
```

### Adding a new tool

1. Create a class that inherits from `BaseTool` in `tools/`.
2. Implement `name`, `schema`, and `execute`.
3. Import and append an instance to `TOOL_REGISTRY` in `tools/__init__.py`.

The agent discovers the new tool automatically.

## Requirements

- Python 3.10+

## Installation

1. Clone the repository or download the folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project root (see `.env.example`):

```
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_preferred_model
```

## Usage

```bash
python content_monitor.py
```

The agent will read feeds, run Google searches, apply keyword filters, and print a consolidated summary of relevant articles.
