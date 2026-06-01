# Clinical Trial Agent

An agentic AI system that answers questions about clinical trials and medical research papers in plain English, grounded in real-time data from ClinicalTrials.gov and PubMed.

---

## What it does

Ask a question about any medical condition and the agent will search live databases, consolidate the top results, and return a clear, synthesized answer — no need to navigate complex medical databases yourself.

**Example queries**
- "What are the latest clinical trials for diabetes?"
- "What does recent research say about treatment options for Alzheimer's?"
- "Are there any active trials for Type 1 diabetes in adolescents?"

---

## Architecture

```
User Query
    │
    ▼
LangGraph Agent (Qwen2.5-72B via HuggingFace Inference API)
    │
    ├──► search_trials (ClinicalTrials.gov API)
    │
    └──► search_pubmed (PubMed API)
    │
    ▼
Synthesized Answer
```

The agent uses a **ReAct loop** — it reasons about the query, decides which tools to call (sometimes both in parallel), processes the results, and synthesizes a final answer. Tools are exposed as MCP servers and connected to the agent via `langchain-mcp-adapters`.

---

## Tech stack

| Component | Choice | Reason |
|---|---|---|
| Agent framework | LangGraph | Fine-grained control over graph nodes and edges; built from scratch rather than using `create_react_agent` |
| LLM | Qwen2.5-72B-Instruct | Strong tool-calling support; available on HuggingFace free Inference API |
| Tool protocol | MCP (Model Context Protocol) | Standardised interface between LLM and external APIs; forward-compatible with other MCP-enabled systems |
| ClinicalTrials.gov | REST API v2 | Official source; structured JSON with trial metadata |
| PubMed | NCBI E-utilities API | Official source; two-step search (IDs → summaries) with rate limiting via `asyncio.Semaphore` |
| MCP ↔ LangChain bridge | langchain-mcp-adapters | Converts MCP tool definitions into LangChain-compatible tool objects |

---

## Key engineering decisions

**1. LangGraph from scratch vs `create_react_agent`**
Built the graph manually (state, agent node, tool node, conditional edges) rather than using the prebuilt helper. This gives full visibility into the reasoning loop and makes the architecture explainable in interviews and system design discussions.

**2. Token cost optimisation**
Initial runs consumed ~18,000 tokens per query by returning full study records. Reduced to ~2,800 tokens (85% reduction) by limiting API responses to the top 3 results and removing fields (detailed descriptions, full eligibility text) not needed for synthesis.

**3. MCP as the tool interface**
Tools are implemented as MCP servers rather than plain Python functions. This makes them reusable across different agent frameworks and aligns with how production AI systems are increasingly being built.

---

## Setup

**Prerequisites**
- Python 3.11
- `uv` (recommended) or `pip`

**Install dependencies**
```bash
uv sync
```

**Environment variables**

Create a `.env` file based on `.env.example`:
```
HUGGINGFACEHUB_API_TOKEN=your_token_here
```

**Run**
```bash
uv run main.py
```

---

## Project structure

```
clinical_trial_agent/
├── main.py                          # Entry point; MCP session and agent invocation
├── Agent/
│   └── agent.py                     # LangGraph graph definition
├── MCP/
│   └── clinical_research_server.py  # MCP server with search_trials and search_pubmed tools
├── .env.example
└── README.md
```

---

## Limitations and next steps

- No persistent memory across sessions
- Results limited to top 3 per source to manage token cost — hardcoded; planned as a configurable parameter
- Deployment via FastAPI + HuggingFace Spaces (in progress)
- Streamlit UI planned 