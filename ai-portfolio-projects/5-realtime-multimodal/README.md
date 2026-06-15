# Project 5 — Real-Time Multimodal Application

Demonstrates you can handle the unique challenges of **streaming data**, **tight latency budgets**, and the **inherent messiness** of systems that respond in real time (not comfortable batch processing).

## Pick One Track

1. **Voice assistant** *(recommended)* — audio input → **ASR** → **LLM** reasoning → **TTS** speech output.
   - *Why this one:* voice AI is experiencing remarkable growth and tooling has matured significantly.
2. **Computer vision pipeline** — webcam feed → **object detection** model → LLM reasons about what's detected.
3. **Streaming log analyzer** — ingest server logs in real time → **anomaly detection** → LLM generates human-readable explanations of what's going wrong.

---

## Recommended Stack (Voice Track)

| Component | Tool |
|-----------|------|
| Speech recognition (ASR) | **Deepgram** or **Whisper** |
| Reasoning | Any capable LLM |
| Speech synthesis (TTS) | **ElevenLabs** or **Cartesia** |
| Pipeline orchestration | **WebSockets** |

> **MERN note:** WebSocket orchestration plays directly to your Node strengths.

---

## Phase 1 — Streaming Pipeline End-to-End

- Just focus on getting it **functioning** — don't optimize yet.
- Goal: get data flowing in, structure your events properly, LLM responding in real time.
- Getting this to work **at all** is a meaningful accomplishment.

## Phase 2 — Latency Tracking
*(The part that demonstrates the most engineering maturity.)*

- **Decompose end-to-end latency into a detailed budget.** For a voice assistant, separately measure:
  - **ASR latency**
  - **LLM time to first token**
  - **TTS time to first byte**
  - All the overhead in between
- Build a **visualization** showing this breakdown for **every request**.

> Being able to say *"our total response time is 1.2s, and here's exactly how that breaks down per component"* is what makes interviewers genuinely excited — it shows you understand performance engineering.

## Phase 3 — Resilience (What Happens When Things Go Wrong)

- What does the system do when the **ASR service goes down**?
- What happens when the **LLM times out**?
- **Graceful degradation** — fall back to a simpler response, or openly acknowledge a delay rather than hanging silently.
- Implement **timeout handling** so nothing blocks indefinitely.
- Build a **replay mode** — feed recorded input back through the pipeline for debugging.

> This is how real production systems are designed. Showing you've thought about **failure modes and recovery** puts you in a completely different category from someone who only builds happy-path versions.

---

## What to Mention in Your Write-Up

- Which track you chose and why.
- Architecture diagram of the streaming pipeline.
- The **latency budget breakdown** visualization, with real numbers per component.
- Your resilience strategies (timeouts, graceful degradation, replay mode) with an example of a simulated failure being handled.
- Total end-to-end latency achieved and where the bottleneck was.
