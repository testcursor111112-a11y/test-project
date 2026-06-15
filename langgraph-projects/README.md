# LangGraph Projects — Simple to Advanced

Seven runnable notebooks, each one real-life use case, each building on the last.

| # | Notebook | Concept | Real-life example |
|---|----------|---------|-------------------|
| 1 | `1_basics_linear_pipeline.ipynb` | State, nodes, edges, compile | Support email pipeline (extract → draft → score) |
| 2 | `2_conditional_routing.ipynb` | Conditional edges, routers | Support ticket triage (billing/technical/general) |
| 3 | `3_chatbot_with_memory.ipynb` | Checkpointers, threads, MessagesState | Pizza shop order bot that remembers customers |
| 4 | `4_agent_with_tools.ipynb` | Tools, ToolNode, ReAct cycle | Trip assistant (weather + currency math) |
| 5 | `5_human_in_the_loop.ipynb` | interrupt() / Command(resume) | Outreach email approval before sending |
| 6 | `6_multi_agent_supervisor.ipynb` | Supervisor pattern, Command(goto) | Content studio (researcher → writer → editor) |
| 7 | `7_product_support_desk.ipynb` | **Everything combined — sellable product** | SupportPilot AI: e-commerce support desk (triage → specialist agents → refund approval gate → analytics) |

## Concept ladder

```
1. graph mechanics  →  2. branching  →  3. memory  →  4. agency (tools)
            →  5. human control  →  6. teams of agents  →  7. the product
```

## Setup

Dependencies already in `pyproject.toml` (`langgraph>=1.2.4`, `langchain-google-genai`).
Needs `GOOGLE_API_KEY_1` (or `GOOGLE_API_KEY`) in the repo's `.env` — already present.

```bash
uv sync
uv run jupyter lab langgraph-projects/
```

Run notebooks in order — each assumes the vocabulary of the previous one.


Project-idea videos (job-focused)

  - 10 AI Projects That Will Land You a Job 2025 (ML/DL/GenAI) — https://www.youtube.com/watch?v=8vSLgY55Bc0
  - Stop Watching Tutorials — Build These 6 AI Projects to Get Hired — https://www.youtube.com/watch?v=uciWAw7XKM0

  RAG (your Tier 1)

  - What is RAG? Build Local AI Agent w/ LangChain + Ollama (full) — https://www.youtube.com/watch?v=4PhVS4VpEbA
  - Build RAG LLM App in 20 min (Langflow, Tech With Tim) — https://www.youtube.com/watch?v=rz40ukZ3krQ
  - Build Scalable RAG System (full architecture) — https://www.youtube.com/watch?v=4KiiKQ9RVvA
  - Build Your First RAG App (LLM Zoomcamp, Alexey Grigorev) — https://www.youtube.com/watch?v=KSItlTAsMsk

  Agents (your Tier 2)

  - Custom RAG agent w/ LangGraph (LangChain docs, has video) — https://docs.langchain.com/oss/python/langgraph/agentic-rag

  Mega-resource (best — 100+ runnable apps)

  - awesome-llm-apps — 100+ AI Agent & RAG apps, full source, clone+ship — https://github.com/Shubhamsaboo/awesome-llm-apps
  - LLM-RAG-Agent-Tutorial (syllabus + MCP) — https://github.com/mac999/LLM-RAG-Agent-Tutorial

  Text idea-lists (not video)

  - GeeksforGeeks 30+ AI projects + source code
  - Simplilearn 20+ trending AI projects

  Sources:
  - Best AI project ideas 2025
  - RAG/agent tutorials search
