# Project 1 — Production-Grade RAG

A **domain-specific "ask my docs" system** that retrieves the right information and answers questions **with proper citations**.

> The gap between a RAG *demo* and a RAG system that is actually *production ready* is enormous. That gap is exactly where you differentiate yourself.

The key word is **citations** — anyone can make an LLM generate a plausible answer; grounding that answer in actual retrieved evidence is what makes it trustworthy.

## What to Build

Pick a corpus of documents in a domain that interests you:
- Technical documentation
- Research papers
- Legal contracts
- Healthcare documents

Build a system that retrieves relevant info and answers questions, pointing to the **exact paragraph** the answer came from.

---

## Phase 1 — Fundamentals Working

- **Ingest** documents (PDF, Markdown, or web pages).
- **Chunk** them into pieces of **~500–800 tokens** with **~100 tokens overlap** between chunks.
  - *Why overlap matters:* you don't want to slice an important sentence at the boundary and lose context.
- Store chunks as **embeddings** in a **vector store** (Chroma or Weaviate — both great to start).
- Build a **retrieval pipeline** that pulls the **top-k** most relevant chunks for a query and generates an answer that **cites where the information came from**.

**Deliverable:** Show a document → show the answer your system produced → point to the exact paragraph it drew from.

## Phase 2 — Demo → Production Quality
*(Most people never get here — which is exactly why it's valuable.)*

- **Hybrid retrieval** = traditional **BM25 keyword search** + **vector semantic search**.
  - *Why both:* vector search understands meaning/intent; BM25 nails specific terms/phrases.
- **Cross-encoder re-ranker** — takes initial retrieved chunks and rescores them by evaluating query + chunk together as a pair. Consistently, dramatically improves precision.
- **Citation enforcement** — system explicitly **declines to answer** if retrieved chunks don't support a response, rather than hallucinating something plausible.
- **Version your prompts** in a config file — prompts are part of system architecture; treating them that way shows engineering maturity.

## Phase 3 — Truly Shippable

- Curate a **golden evaluation dataset** of **~50–200 Q&A pairs**, manually verified for correctness.
- Write an **offline evaluation script** that measures **faithfulness** — *are the claims in the generated answer actually supported by the retrieved chunks?*
- **Wire eval into CI** — every pull request automatically triggers an evaluation run. **If quality drops below threshold, the build fails.**
  - This is exactly how production AI teams operate. Visible in your portfolio = signals you understand the full lifecycle.

---

## Recommended Tech Stack

| Concern | Tool |
|---------|------|
| Orchestration | LangChain or LangGraph |
| Vector store | ChromaDB or Weaviate |
| Re-ranking | Cohere reranker, or cross-encoder models from `sentence-transformers` |
| Evaluation | **ragas** (purpose-built for assessing RAG systems) |

> **MERN + Supabase note:** You can use Supabase **`pgvector`** as the vector store instead of Chroma — you already run Supabase, so this is a strong, differentiated choice.

## What to Mention in Your Write-Up

- The domain + corpus you chose and why.
- Chunking strategy (size, overlap) and the reasoning.
- Before/after precision improvement from adding the re-ranker.
- Your golden eval set, faithfulness scores, and a screenshot of the **CI gate failing** on a bad change.
- A worked example: question → retrieved chunks → cited answer.
