# Project 2 — Local Offline AI Assistant (Small LLM)

An AI assistant that runs **entirely offline** using a small language model. More important than most people realize.

## Why Bother (vs. just calling GPT-5)?

Real-world scenarios where you **cannot or shouldn't** send data to an external service:
- **Privacy regulations** (data can't leave the premises).
- **Latency requirements** that rule out network round-trips.
- **Cost constraints** at scale.
- **Edge deployment** where internet connectivity isn't guaranteed.

Companies care deeply about these constraints — and **most candidates have zero hands-on experience** navigating them.

---

## Phase 1 — Get It Running + Measure

- Install **Ollama** — simplest way to run an open-source model locally.
- Pull a model in the **3–7B parameter** range: **Llama 3.2**, **Phi-4**, or **Mistral 7B**.
- Build a **CLI tool** or a **FastAPI wrapper** around it.

**Most important in Phase 1 = measurement.** Rigorously benchmark inference performance and put the numbers in your docs:
- Tokens per second
- Time to first token
- Total response latency

> These numbers tell a story about the practical trade-offs of local inference.

## Phase 2 — Structure + Determinism

- **Enforce a JSON output schema** on responses.
- **Validate with Pydantic.**
- **Retry mechanism** — catch invalid outputs, re-prompt once, then fail gracefully.
  - This *constrain → validate → retry* pattern is everywhere in production and **rare in portfolios**.
- **Temperature experiment** — run the same prompts at **temperature 0 vs 0.7** and document the variance.
  - Shows you understand the stochastic nature of LLMs and how to control it when reliability matters.

## Phase 3 — Model Comparison Study
*(Possibly the most impressive deliverable of the project.)*

- Pick **three models**, e.g. **Llama 3.2 3B**, **Phi-4 mini**, **Mistral 7B**.
- Benchmark all on the **same hardware**.
- Compare:
  - Memory usage
  - Tokens per second
  - **Output quality** on a standardized set of **30–50 test prompts**
- Write a concise **technical report** with actual numbers and analysis.

> Model selection is a decision every AI team makes regularly. Approaching it **systematically with data** (not "what's popular on X/LinkedIn") tells a hiring manager you think like an engineer.

**Extra mile:** Try **quantized** versions (GGUF **Q4** / **Q5**) and document the **quality-vs-speed trade-off**.

---

## What to Mention in Your Write-Up

- Hardware specs (so benchmarks are reproducible).
- Full benchmark table: model × {memory, tokens/sec, latency, quality score}.
- The JSON schema + Pydantic validation + retry logic, with an example of a caught/retried failure.
- Temperature 0 vs 0.7 output comparison.
- Quantization trade-off findings (if attempted).
- A clear recommendation: *"For task X under constraint Y, I'd pick model Z because…"*
