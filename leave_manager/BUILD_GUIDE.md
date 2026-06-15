# Leave Manager Chatbot — Build Guide

A LangGraph chatbot that answers leave questions from a sheet and updates the sheet when employees email leave requests.

## Why LangGraph

Two distinct flows plus a write that touches real data:

- **Read flow**: user asks a leave question → query sheet → answer.
- **Write flow**: employee email arrives → parse → validate → update sheet.

LangGraph fits because it gives:
- Conditional routing between the read and write flows.
- Persistent state across steps.
- A **human-in-loop approval gate before any sheet write** — critical, since an LLM mis-parsing an email could corrupt leave records.

A plain tool-calling agent would work too, but LangGraph makes the write gate explicit and controllable.

---

## Step-by-step

### 1. Pick sheet backend + access
- Google Sheets via `gspread` + service account, or the Sheets API.
- Lock the schema now. Columns: `employee_id, name, leave_type, start_date, end_date, days, status, balance`.
- Agent reliability depends on a stable schema.

### 2. Build sheet tools (plain functions first, no LLM)
- `read_leaves(employee=None)` → rows
- `get_balance(employee)`
- `append_leave(record)`
- `update_leave(row_id, fields)`
- Test these standalone. They must work 100% before wiring the agent.

### 3. Define LangGraph state
Fields:
- `messages`
- `intent` (query / leave_request)
- `parsed_leave`
- `pending_write`
- `approved`

### 4. Router node
- Classify input: question vs leave-email.
- Conditional edge → query branch or write branch.

### 5. Query branch (read-only)
- Node: LLM + read tools → answer.
- No approval needed.

### 6. Write branch (email → sheet)
- **Node A — parse**: extract `employee, leave_type, dates, days` from the email. Use structured output (schema), not free text.
- **Node B — validate**: employee exists? enough balance? date overlap? dates sane?
- **Node C — human-in-loop interrupt**: show the parsed record, wait for approve/reject. Use LangGraph `interrupt()`.
- **Node D — commit**: on approve → `append_leave` + decrement balance. On reject → end.

### 7. Email ingestion (separate from the graph)
- IMAP / Gmail API poll inbox → feed body into the graph as a `leave_request`.
- Keep ingestion OUTSIDE graph logic. The graph processes one event; ingestion just delivers events.

### 8. Persistence
- LangGraph checkpointer (SQLite to start) so interrupt/resume works across the approval wait.

### 9. Interface
- CLI or Slack/web for Q&A.
- Approval step can route to the same channel.

### 10. Guardrails
- Never write without a validation pass + approval.
- Log every sheet mutation (who, what, when) to a separate audit tab.
- Concurrency: serialize or lock writes — two simultaneous leaves race on balance.

---

## Build order
1. Step 2 (tools)
2. Step 5 (query, read-only — easy win)
3. Step 6 (write — hardest, most risk)
4. Step 7 (email)

Get read working end-to-end before touching writes.

**Biggest risk**: email parsing wrong → bad write. That is why steps 6B + 6C exist. Do not skip the approval gate early on.
