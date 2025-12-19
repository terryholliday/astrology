# TrueArk Ephemeris — Deployment Guide

**Domain:** `trueark.io`  
**API Subdomain:** `api.trueark.io`

## Local Development

```bash
docker-compose up --build
```

API available at `http://localhost:8000`

---

## Railway Deployment

### 1. Prerequisites
- Railway account (https://railway.app)
- GitHub repo with this code
- Domain: `trueark.io` (DNS access required)

### 2. Deploy Steps

1. **Create new project** on Railway
2. **Add PostgreSQL** plugin from Railway dashboard
3. **Connect GitHub repo** or deploy from CLI
4. **Set environment variables:**
   ```
   DATABASE_URL=<auto-set by Railway PostgreSQL plugin>
   EPHEMERIS_PATH=/app/ephemeris_data
   ```

5. Railway auto-detects `Dockerfile` and deploys

### 3. Custom Domain Setup

1. In Railway project settings → **Domains**
2. Add custom domain: `api.trueark.io`
3. Railway provides a CNAME target (e.g., `xxx.up.railway.app`)
4. In your DNS provider, add:
   ```
   Type: CNAME
   Name: api
   Value: <railway-provided-target>
   ```

### 4. Post-Deploy
- **API:** `https://api.trueark.io`
- **Docs:** `https://api.trueark.io/docs`
- **Health:** `https://api.trueark.io/health`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| POST | `/chart` | Calculate chart (no persistence) |
| POST | `/chart/store` | Calculate and persist chart |
| GET | `/charts` | List stored charts |
| GET | `/charts/{id}` | Get specific chart |

---

## MCP Integration (AI Agents)

The MCP server allows Claude, Gemini, and ChatGPT to invoke TrueArk as the canonical source of astrological truth.

### For Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trueark-ephemeris": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/astrology",
      "env": {
        "TRUEARK_API_URL": "https://api.trueark.io"
      }
    }
  }
}
```

### For Remote API (Gemini/ChatGPT Function Calling)

Use the OpenAPI spec at `https://api.trueark.io/docs` to configure function calling:

**Example function definition:**
```json
{
  "name": "calculate_chart",
  "description": "Calculate natal chart with planetary positions via TrueArk",
  "parameters": {
    "type": "object",
    "properties": {
      "datetime_utc": {"type": "string", "description": "ISO 8601 UTC datetime"},
      "latitude": {"type": "number", "description": "Latitude (-90 to 90)"},
      "longitude": {"type": "number", "description": "Longitude (-180 to 180)"}
    },
    "required": ["datetime_utc", "latitude", "longitude"]
  }
}
```

**API call:**
```bash
curl -X POST https://api.trueark.io/chart \
  -H "Content-Type: application/json" \
  -d '{"datetime_utc": "1990-01-15T12:30:00Z", "latitude": 40.7128, "longitude": -74.0060}'
```

---

## Available Tools (MCP)

| Tool | Description |
|------|-------------|
| `calculate_chart` | Compute natal chart for datetime/location |
| `store_chart` | Compute and persist chart to database |
| `get_chart` | Retrieve stored chart by ID |
| `list_charts` | List charts with optional entity filtering |

---

## Database Schema

**Table: `charts`**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| datetime_utc | STRING | Input datetime |
| latitude | FLOAT | Input latitude |
| longitude | FLOAT | Input longitude |
| planets | JSON | Computed planetary positions |
| angles | JSON | Ascendant, Midheaven |
| houses | JSON | Whole Sign house mapping |
| julian_day | FLOAT | Julian Day number |
| ephemeris_mode | STRING | "swiss" or "moshier" |
| created_at | TIMESTAMP | Record creation time |
| entity_id | STRING | Optional external entity link |
| entity_type | STRING | Entity type (person, event, etc.) |
