# OpenAPI2MCP

Generate an OpenAPI-to-MCP server, then run it either over stdio or HTTP.

## What’s in this repo

- `src/openapi2mcp/` — the generator package used by `openapi2mcp`
- `example/` — generated Petstore output
- `pyproject.toml` — project metadata for `uv` / editable installs

## Prerequisites

- Python 3.10+
- `uv` installed locally
- Node.js only if you want to open the MCP Inspector

## Setup

```bash
uv venv
uv sync
```

If you prefer plain `venv`, this also works:

```bash
python -m venv .venv
.venv\Scripts\pip install -e .
```

## Generate a server

Use the CLI with an OpenAPI URL or a local spec file:

```bash
uv run openapi2mcp generate --spec https://petstore3.swagger.io/api/v3/openapi.json --out example --name petstore
```

That creates a runnable MCP server in `example/`.

## Run the generated server

### HTTP transport

```bash
cd example
..\.venv\Scripts\python.exe server.py --transport http --host 127.0.0.1 --port 8765
```

The MCP endpoint will be available at:

```text
http://127.0.0.1:8765/mcp
```

### stdio transport

```bash
cd example
..\.venv\Scripts\python.exe server.py
```

This mode is meant to be launched by an MCP client, not run interactively in a terminal.

## Environment variables

- `API_BASE_URL` — base URL of the real API
- `API_KEY` — optional API key or token value
- `AUTH_HEADER` — header name for the API key, defaults to `Authorization`

Example:

```bash
set API_BASE_URL=http://localhost:8000
set API_KEY=your-token
```

## Open the MCP Inspector

The Inspector is documented by MCP as a Node-based tool. If Node.js is installed, you can open the generated server like this:

```bash
npx @modelcontextprotocol/inspector http://127.0.0.1:8765/mcp
```

For locally developed Python servers, the official guide also shows using `uv` through the Inspector wrapper.

## Notes

- The generated `example/README.md` is the server-specific guide for the Petstore output.
- `example/server.py`, `example/tools.py`, and `example/executor.py` should stay together in the same directory.
