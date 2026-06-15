# AI Engineering Portfolio — 5 Projects (2026)

Five portfolio projects that signal to a hiring manager: *"This person understands how production AI systems actually work"* — not tutorial chatbots.

Source: YouTube video by Ashwarashan (ex-Microsoft / Google / IBM, led AI DevRel at Fireworks AI). Each project targets a distinct, in-demand skill. Together they tell a cohesive story of who you are as an AI engineer.

## The Projects

| # | Project | Core Skill Signaled |
|---|---------|--------------------|
| 1 | [Production-Grade RAG](./1-production-rag/) | Retrieval, grounding, evaluation, CI gating |
| 2 | [Local Offline LLM Assistant](./2-local-llm-assistant/) | Small models, constrained generation, benchmarking |
| 3 | [RAG Observability Layer](./3-rag-observability/) | Tracing, metrics, SRE-for-AI thinking |
| 4 | [Fine-Tuning with LoRA/DPO](./4-fine-tuning-lora/) | When/why to fine-tune, measurable gains |
| 5 | [Real-Time Multimodal App](./5-realtime-multimodal/) | Streaming, latency budgets, resilience |

## Suggested Order (for a MERN + Python + Supabase dev)

1. **Project 1 (RAG)** — Python + Supabase `pgvector` covers this directly. Start here.
2. **Project 3 (Observability)** — builds on Project 1. High differentiation, almost nobody does it.
3. **Project 5 (Voice/Multimodal)** — Node + WebSockets plays to MERN strengths.
4. **Project 2 (Local LLM)** — stretch.
5. **Project 4 (Fine-tuning)** — stretch, do last.

## Why This Portfolio Works

- Market: "AI Engineer" is LinkedIn's #1 fastest-growing US job (postings +143% YoY). Hiring shifted from *model-focused* to *systems-focused*.
- Each project shows the **full lifecycle** of an AI system — build, evaluate, monitor, ship — not just a happy-path demo.
- The gap between a demo and a production system is exactly where you differentiate.

## General Resume / Portfolio Tips (apply to every project)

- Treat **prompts as architecture** — store them in versioned config files, not hardcoded strings.
- Always include **real numbers** — latency, cost, accuracy. Data beats adjectives.
- **Honestly document what went wrong** and how you iterated. Hiring managers love troubleshooting evidence.
- Wire quality checks into **CI** wherever possible — it proves engineering discipline.
