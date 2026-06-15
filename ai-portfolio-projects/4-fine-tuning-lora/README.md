# Project 4 — Fine-Tuning (LoRA + DPO)

A fine-tuning project with **measurable before/after improvements**.

## Set Expectations First

> Fine-tuning is **not** about making a model generally smarter. It's about making a model **consistently excellent at a specific, well-defined task** where even careful prompting falls short.

Before you fine-tune anything, you need a clear task where you can **credibly demonstrate the gap**:
- Here's the best the **base model** can do with the most carefully engineered prompt.
- Here's the **measurable improvement** after fine-tuning.

## Recommended Tasks

Pick one where fine-tuning gives clear, quantifiable gains:
- **Structured JSON extraction** from messy unstructured text.
- **Tool-call accuracy** — model selects the right function and populates the correct parameters.

---

## Phase 1 — Supervised Fine-Tuning (SFT) with LoRA

- Start with a **clean dataset** of **~2,000–10,000 examples**.
  - **Data quality >> quantity.** Inconsistent or poorly formatted examples teach the model to be inconsistent and poorly formatted.
- Use **LoRA** or **QLoRA** for parameter-efficient fine-tuning — no massive GPU cluster needed.
  - A single **A100**, or even a **T4 with QLoRA**, gets the job done.
- Suggested base model: **Qwen 3 8B**.
- Evaluate on a **held-out dataset** with concrete metrics:
  - **JSON validity rate**
  - **Exact-match accuracy**
  - **Refusal correctness** — does the model properly decline when it should?

## Phase 2 — Preference Tuning (DPO)
*(Demonstrates understanding beyond the basics.)*

- Instead of only showing the correct output, show **comparisons**: for the same input, *here's a good output, here's a worse one — learn the difference.*
- Generate **multiple outputs per prompt**, label better vs. worse.
- Train using **DPO-style preference optimization**.
- Re-evaluate on your test set and show the **incremental improvement over the SFT baseline**.

> Demonstrates familiarity with modern alignment/training techniques used in industry today.

**Note:** All fine-tuning steps are **stackable** — they layer one on top of the other (SFT → DPO).

---

## Recommended Tech Stack

| Concern | Tool |
|---------|------|
| SFT + DPO training | Hugging Face **TRL** |
| Config-driven training | **Axolotl** (takes config complexity off your plate) |
| GPU compute (no infra hassle) | **Fireworks AI** |

## What to Mention in Your Write-Up

- The task and the **demonstrated gap** (base-model-with-best-prompt vs. fine-tuned).
- **Show the training curve.**
- Present **before/after metrics** very clearly (JSON validity, exact match, refusal correctness, DPO lift over SFT).
- **Honestly discuss what went wrong** during the process and how you iterated past it — hiring managers love seeing that you can troubleshoot and adapt, because that's what day-to-day work actually looks like.
