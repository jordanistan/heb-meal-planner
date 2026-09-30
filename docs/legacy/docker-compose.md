Running Playwright with persistent browser sessions inside a containerized setup is cleanest when configured as an **SSE (Server-Sent Events) HTTP service**. This avoids stdio proxying issues across container boundaries and allows both Claude Desktop (via an SSE bridge or direct SSE client) and other local services to invoke it over your internal network.

Here is the production-ready container setup, including support for both **SSE transport** and **stdio mode via `docker exec**`.

---

### Project Structure

```text
heb-mcp-server/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── server.py
└── data/                 # Mounted persistent browser profile & cache
    └── heb_user_data/

```

---

### 1. Updated `requirements.txt`

FastMCP supports SSE transport over Uvicorn / Starlette:

```text
mcp>=1.0.0
playwright>=1.49.0
playwright-stealth>=1.0.6
pydantic>=2.0.0
uvicorn>=0.30.0
starlette>=0.38.0

```

---

### 2. Transport-Flexible `server.py`

Modify the entry point of your `server.py` to allow toggling between `stdio` and `sse` via environment variables:

```python
import os
from server import mcp  # Assumes your FastMCP instance from the previous step

# Override user data directory to match the container's volume mount
BASE_DIR = os.getenv("HEB_DATA_DIR", "/app/data/heb_user_data")

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "sse").lower()
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    if transport == "sse":
        print(f"Starting HEB MCP Server on SSE transport at http://{host}:{port}/sse")
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run(transport="stdio")

```

---

### 3. `Dockerfile`

This uses Microsoft’s official Playwright runtime container, which includes all necessary OS dependencies, fonts, and Chromium dependencies for headless execution without missing library errors.

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Prevent interactive prompts and Python bytecode writes
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HEB_DATA_DIR=/app/data/heb_user_data

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Chromium browser binaries are installed
RUN playwright install chromium

# Copy application files
COPY . .

# Create the persistent data directory
RUN mkdir -p /app/data/heb_user_data

# Expose the default FastMCP SSE port
EXPOSE 8000

# Default command launches SSE transport
CMD ["python3", "server.py"]

```

---

### 4. `docker-compose.yml`

```yaml
services:
  heb-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: heb-mcp-server
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - MCP_TRANSPORT=sse
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
      - HEB_DATA_DIR=/app/data/heb_user_data
    volumes:
      # Persists H-E-B cookies, local store selection, and session tokens
      - ./data/heb_user_data:/app/data/heb_user_data
      # Shared memory allocation to avoid Chromium crashes on heavy DOM renders
    shm_size: "1gb"
    security_opt:
      - seccomp:unconfined

```

---

### 5. Managing Persistent Context & Store Selection

Because H-E-B dynamically adapts catalog items and prices based on the assigned store, run an interactive browser pass once on your host or directly inside the container to seed `./data/heb_user_data`.

#### Option A: Seed directly via your host Playwright

If you have Playwright on your host:

```bash
playwright launch --persistent-context ./data/heb_user_data https://www.heb.com

```

Select your preferred store, set your zip code, and close the browser.

#### Option B: Seed headlessly via container run

Alternatively, launch a temporary container instance with the UI forwarded or script a quick location selection directly into the mounted volume.

---

### 6. Integrating with Claude Desktop

Depending on whether you want to use the **SSE endpoint** or direct **container stdio execution**:

#### Method A: Using SSE (Recommended)

Start the service:

```bash
docker compose up -d --build

```

If your client supports remote or local SSE MCP endpoints directly, configure it to target:

```text
http://127.0.0.1:8000/sse

```

If using a Node-based SSE-to-stdio bridge (such as `mcp-remote`):

```json
{
  "mcpServers": {
    "heb-grocery": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://127.0.0.1:8000/sse"
      ]
    }
  }
}

```

#### Method B: Using Container Stdio (`docker exec`)

If you prefer not to keep an HTTP daemon running and want Claude Desktop to invoke the container process directly via `stdio`:

Change `MCP_TRANSPORT=stdio` or use `docker exec`:

```json
{
  "mcpServers": {
    "heb-grocery": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "-e",
        "MCP_TRANSPORT=stdio",
        "heb-mcp-server",
        "python3",
        "server.py"
      ]
    }
  }
}

```

*(Requires `heb-mcp-server` to be running in the background via `docker compose up -d`).*
