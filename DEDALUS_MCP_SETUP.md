# Dedalus MCP Integration Guide

## What is Dedalus MCP?

**Dedalus MCP (Model Context Protocol)** is a protocol that allows AI assistants to connect to external tools and data sources. It enables:

- **Multi-tool orchestration**: Combine multiple tools (web search, job search, skill matching, etc.)
- **Real-time job research**: Search job boards using MCP tools
- **Resume tailoring**: Use specialized MCP tools for resume customization
- **Skill matching**: Match skills to job requirements using MCP tools

## Integration Status

✅ **MCP Service Created**: `backend/app/services/dedalus_mcp.py`
✅ **Integrated into Dedalus Service**: `backend/app/services/dedalus_svc.py`
✅ **Fallback Support**: Falls back to JSearch API or heuristics if MCP unavailable

## Setup Instructions

### Step 1: Install Dedalus SDK

```bash
cd backend
pip install dedalus
```

**Note:** If Dedalus SDK is not available via pip, you may need to:
- Install from source
- Use Dedalus API directly (HTTP)
- Wait for official SDK release

### Step 2: Get Dedalus API Key

1. Go to: https://dedaluslabs.net/
2. Sign up/login
3. Get your API key from dashboard
4. Add to `.env`:
   ```env
   DEDALUS_API_KEY=your-api-key-here
   ```

### Step 3: Configure MCP Tools

Dedalus MCP uses tools from the MCP Marketplace. Available tools include:

- `dedalus-user-1/web-search-v1`: Web search for job boards
- `dedalus-user-1/job-search-v1`: Dedicated job search tool
- `dedalus-user-1/skill-matcher-v1`: Skill matching tool
- `dedalus-user-1/resume-tailor-v1`: Resume tailoring tool
- `dedalus-user-1/star-formatter-v1`: STAR format bullets
- `dedalus-user-1/cover-letter-v1`: Cover letter generation

**Location:** `backend/app/services/dedalus_mcp.py`

You can customize which tools to use in the `_create_mcp_agent()` method.

### Step 4: Test Integration

1. **Start Backend:**
   ```bash
   cd backend
   make dev
   ```

2. **Test Job Research:**
   ```bash
   curl -X POST http://localhost:8000/jobs/autoResearch \
     -H "Content-Type: application/json" \
     -d '{"target_role": "Software Engineer", "resume_summary": "React, TypeScript, Node.js"}'
   ```

3. **Check Logs:**
   - Look for: `[Dedalus] MCP service available`
   - Look for: `[Dedalus MCP] Initializing: Setting up Dedalus MCP agent`
   - Look for: `[Dedalus MCP] Searching: Searching for positions using MCP`

## How It Works

### Job Research Flow

1. **MCP Agent Creation:**
   ```python
   agent = dedalus.create_agent(
       models=["openai/gpt-4o"],
       tools=["dedalus-user-1/web-search-v1", "dedalus-user-1/job-search-v1"],
       instructions="Find matching jobs..."
   )
   ```

2. **Job Search:**
   ```python
   response = agent.run("Find Software Engineer jobs matching React, TypeScript")
   ```

3. **Result Processing:**
   - Parse MCP response
   - Convert to Job objects
   - Calculate match scores
   - Generate why[] and fix[] arrays

### Resume Tailoring Flow

1. **MCP Agent Creation:**
   ```python
   agent = dedalus.create_agent(
       models=["openai/gpt-4o"],
       tools=["dedalus-user-1/resume-tailor-v1", "dedalus-user-1/star-formatter-v1"],
       instructions="Tailor resumes..."
   )
   ```

2. **Resume Tailoring:**
   ```python
   response = agent.run("Tailor this resume for this job description...")
   ```

3. **Result Processing:**
   - Parse MCP response
   - Extract bullets, pitch, cover letter
   - Convert to TailorResponse object

## Priority Order

The system tries methods in this order:

1. **Dedalus MCP** (if `DEDALUS_API_KEY` is set and SDK is installed)
2. **JSearch API** (if `RAPIDAPI_KEY` is set)
3. **Dedalus API** (if `DEDALUS_API_KEY` is set but SDK not installed)
4. **Fallback Heuristics** (always available)

## Configuration

### Environment Variables

```env
# Dedalus MCP
DEDALUS_API_KEY=your-api-key-here
DEDALUS_MCP_URL=https://api.dedaluslabs.net/mcp  # Optional, defaults to this

# Fallback options
RAPIDAPI_KEY=your-rapidapi-key  # For JSearch API
```

### Customizing MCP Tools

Edit `backend/app/services/dedalus_mcp.py`:

```python
def _create_mcp_agent(self, tools: List[str], instructions: str = None):
    # Customize tools here
    tools = [
        "dedalus-user-1/web-search-v1",
        "dedalus-user-1/job-search-v1",
        "dedalus-user-1/skill-matcher-v1"
    ]
    
    agent = self.dedalus_sdk.create_agent(
        models=["openai/gpt-4o"],  # Can change model
        tools=tools,
        instructions=instructions
    )
    
    return agent
```

## Troubleshooting

### MCP Service Not Available

**Error:** `[Dedalus] MCP service not available`

**Solution:**
1. Check `DEDALUS_API_KEY` is set in `.env`
2. Install Dedalus SDK: `pip install dedalus`
3. Restart backend server

### SDK Import Error

**Error:** `ImportError: No module named 'dedalus'`

**Solution:**
1. Install SDK: `pip install dedalus`
2. If not available, use Dedalus API directly (HTTP)
3. Or wait for official SDK release

### MCP Tools Not Found

**Error:** `Tool not found: dedalus-user-1/web-search-v1`

**Solution:**
1. Check tool names in Dedalus MCP Marketplace
2. Update tool names in `dedalus_mcp.py`
3. Verify you have access to the tools

### Fallback to Other Methods

If MCP fails, the system automatically falls back to:
- JSearch API (if `RAPIDAPI_KEY` is set)
- Dedalus API (if `DEDALUS_API_KEY` is set)
- Internal heuristics (always available)

## Benefits of MCP

1. **Multi-tool Orchestration**: Combine multiple tools for better results
2. **Real-time Updates**: Get live job data from multiple sources
3. **Specialized Tools**: Use dedicated tools for job search and resume tailoring
4. **Flexible Configuration**: Easily add/remove tools as needed
5. **Better Matching**: Use skill matching tools for accurate job matching

## Next Steps

1. **Get Dedalus API Key**: Sign up at https://dedaluslabs.net/
2. **Install SDK**: `pip install dedalus` (when available)
3. **Configure Tools**: Customize MCP tools in `dedalus_mcp.py`
4. **Test Integration**: Run job research and verify MCP is working
5. **Monitor Logs**: Check backend logs for MCP activity

## Resources

- **Dedalus Labs**: https://dedaluslabs.net/
- **MCP Marketplace**: https://dedaluslabs.net/marketplace
- **Documentation**: Check Dedalus documentation for latest SDK usage

