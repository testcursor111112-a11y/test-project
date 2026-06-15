# Project 3 — RAG Monitoring & Observability Layer

Take the **RAG app from Project 1** and add a comprehensive **monitoring and observability** layer. Almost nobody includes this in their portfolio — which is *precisely* why you should.

> In production, building the initial system is maybe **30%** of the work. The remaining **70%** is knowing whether it's working, understanding why it fails, and diagnosing/fixing quickly.

If you can show you think about systems this way, you set yourself apart from the majority of candidates who **only know how to build**.

---

## Phase 1 — Instrument Everything (Tracing)

For **every single request**, you should be able to see:
- Which chunks were retrieved
- How the re-ranker reordered them
- What prompt was sent to the LLM
- What the response was
- How many tokens were consumed

**Tools:** Langsmith, **Langfuse**, or Brain Trust.
- Recommended starter: **Langfuse** — open-source and self-hostable, so no usage limits while experimenting.

## Phase 2 — Track Quality Metrics Over Time
*(Think like a Site Reliability Engineer, but for AI.)*

- **Latency at P50 and P95 percentiles** — not just the average (averages hide worst-case performance).
- **Cost per request** — quantify what each query costs in dollars.
- **Citation coverage** — % of answers properly grounded in retrieved evidence.
- **Failure rate** — how often the system errors out or produces an unsupported response.

**Deliverable:** When someone asks *"what happened when quality degraded last Tuesday?"*, you can pull up a **dashboard**, point to the anomaly, and walk through the root cause.

## Phase 3 — Connect Everything with Regression Gating

- Your **eval dataset from Project 1** now runs automatically in **CI**.
- If **faithfulness** (or any key metric) drops below threshold → **build fails, change doesn't merge**.
- **Version your prompts and config files** alongside your code — a prompt change can alter behavior as dramatically as a code change.

> This operational discipline is what production AI teams practice every day. Rare and impressive in a portfolio.

---

## A Note on Expectations

This project **won't look as flashy** as an image generator or a chatbot with a pretty frontend. But it signals something employers value enormously: **you think about systems holistically, not just the model in the middle.** That system-level thinking is exactly the gap most AI teams are trying to fill.

## What to Mention in Your Write-Up

- Architecture diagram showing where tracing hooks into the RAG pipeline.
- Screenshots of your dashboard (latency P50/P95, cost/request, citation coverage, failure rate).
- A real (or simulated) incident: a quality regression, how you spotted it, and the root cause.
- The CI regression gate config + a screenshot of a blocked merge.
- Why you chose your tracing tool (e.g., Langfuse for self-hosting).
