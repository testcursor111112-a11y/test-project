import os
from pathlib import Path

import gspread
from dotenv import load_dotenv

# project root .env (this file lives at <root>/leave_manager/)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SHEET_KEY = os.getenv("SHEET_ID")
SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT_PATH", "service_account.json")


class LeaveSheet:
    def __init__(self, key=SHEET_KEY, cred=SERVICE_ACCOUNT):
        gc = gspread.service_account(filename=cred)
        self.ws = gc.open_by_key(key).sheet1
        self.reload()

    def reload(self):
        """Pull all values once, build employee->column map."""
        self.rows = self.ws.get_all_values()   # list[list[str]], 0-indexed
        id_row   = self.rows[0]
        name_row = self.rows[1]
        head_row = self.rows[2]

        # block starts = columns where an ID exists (skip col 0)
        starts = [i for i in range(1, len(id_row)) if id_row[i].strip()]
        starts.append(len(id_row))  # sentinel end

        self.employees = {}   # name -> meta
        for b in range(len(starts) - 1):
            c0, c1 = starts[b], starts[b + 1]
            emp_id = id_row[c0].strip()
            name   = name_row[c0].strip()
            # map sub-header -> absolute col index within this block
            fields = {}
            for c in range(c0, c1):
                key = head_row[c].strip().lower()  # credit / lwp / debit
                if key:
                    fields[key] = c
            self.employees[name] = {
                "id": emp_id,
                "col_start": c0,
                "fields": fields,   # {'credit': idx, 'lwp': idx, 'debit': idx}
            }

        # date rows: row index 3.. until first blank date cell
        self.date_rows = {}   # date string -> 0-indexed row
        r = 3
        while r < len(self.rows) and self.rows[r][0].strip():
            self.date_rows[self.rows[r][0].strip()] = r
            r += 1
        self._summary_start = r  # blank line after data

    @staticmethod
    def _num(val):
        """Parse cell to float; keep raw string if it's a note like '(1-26Jan)'."""
        v = val.strip()
        if v in ("", "-"):
            return 0.0
        try:
            return float(v)
        except ValueError:
            return v   # annotation, keep raw

    # ---- READ ----
    def list_employees(self):
        print("listing employees")
        return list(self.employees.keys())

    def get_all_data(self):
        """Everything: employee -> date -> {credit,lwp,debit}."""
        out = {}
        for name in self.employees:
            out[name] = self.get_employee(name)
        
        print("get_all_data")
        return out

    def get_employee(self, name):
        meta = self.employees[name]
        data = {"id": meta["id"], "leaves": {}}
        for date, r in self.date_rows.items():
            row = self.rows[r]
            rec = {}
            for f, c in meta["fields"].items():
                raw = row[c] if c < len(row) else ""
                rec[f] = self._num(raw)
            data["leaves"][date] = rec

        print('get_employee')
        return data

    def get_balance(self, name):
        """Read 'Leave Balance' row value for employee."""
        meta = self.employees[name]
        for r in range(self._summary_start, len(self.rows)):
            if self.rows[r] and self.rows[r][0].strip().lower() == "leave balance":
                c = meta["col_start"]
                return self._num(self.rows[r][c]) if c < len(self.rows[r]) else 0.0
    
        print("get_balance")
        return None

    # ---- WRITE ----
    def set_value(self, name, date, field, value):
        """field = 'credit' | 'lwp' | 'debit'. Writes one cell."""
        meta = self.employees[name]
        if field.lower() not in meta["fields"]:
            raise ValueError(f"{name} has no '{field}' column")
        if date not in self.date_rows:
            raise ValueError(f"date '{date}' not found")
        r = self.date_rows[date]            # 0-indexed
        c = meta["fields"][field.lower()]   # 0-indexed
        self.ws.update_cell(r + 1, c + 1, value)   # gspread is 1-indexed
        self.rows[r][c] = str(value)               # keep cache in sync

    def add_leave(self, name, date, days, field="debit"):
        """Add `days` to existing value (e.g. employee took leave)."""
        cur = self.get_employee(name)["leaves"].get(date, {}).get(field, 0.0)
        if not isinstance(cur, (int, float)):
            raise ValueError(f"cell has note '{cur}', fix manually")
        self.set_value(name, date, field, cur + days)

    def resolve_month(self, month):
        """Match a loose month string to the stored date-row key.

        Accepts 'jun', 'June', 'Jun 2026', '1 Jun 2026', etc.
        Returns the exact stored key (e.g. '1 Jun 2026') or raises."""
        q = month.strip().lower()
        keys = list(self.date_rows.keys())
        # exact match first
        for k in keys:
            if k.lower() == q:
                return k
        # token-subset match: every word in query appears in the key
        q_words = q.replace(",", " ").split()
        matches = [
            k for k in keys
            if all(w in k.lower() for w in q_words)
        ]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ValueError(f"no month row matches '{month}'. Available: {keys}")
        raise ValueError(f"'{month}' ambiguous, matches {matches}")


# ---------------------------------------------------------------------------
# LLM TOOLS
# ---------------------------------------------------------------------------
# Wrap LeaveSheet methods as langchain tools so an LLM can call them.
# One lazily-created shared sheet so we open the spreadsheet only once.

from langchain_core.tools import tool

_sheet = None


def get_sheet() -> "LeaveSheet":
    """Return the shared LeaveSheet, opening the spreadsheet on first use."""
    global _sheet
    if _sheet is None:
        _sheet = LeaveSheet()
    return _sheet


@tool
def list_employees() -> list[str]:
    """List the full names of all employees tracked in the leave sheet.
    Call this first when you need an exact name to pass to other tools."""

    print('list_employees')
    return get_sheet().list_employees()


@tool
def get_employee_leaves(name: str) -> dict:
    """Get every leave record for one employee.

    Args:
        name: exact employee full name (use list_employees to get valid names).
    Returns a dict: {"id": str, "leaves": {date: {credit, lwp, debit}}}.
    Dates look like '1 Jun 2026'."""    
    sheet = get_sheet()
    sheet.reload()          # pull live values
    return sheet.get_employee(name)
@tool
def get_leave_balance(name: str) -> float | None:
    """Get the current 'Leave Balance' number for one employee. the data is constantly changing so pelase call this tool every time when user asks for his leave balance.

    Args:
        name: exact employee full name.
    Returns the balance as a float, or null if no balance row exists."""
    return get_sheet().get_balance(name)


@tool
def record_leave(name: str, month: str, days: float, field: str = "debit") -> str:
    """Record leave by ADDING days to an existing month cell (does not overwrite).

    The exact date is NOT needed — leave is tracked per month. Pass just the
    month and the matching row is resolved automatically.

    Args:
        name: exact employee full name.
        month: the leave month, loose form is fine: 'Jun', 'June', 'Jun 2026'. make sure it should be like '1 Jun 2026', means it should have first date the month.
        days: number of days to add (e.g. 1.0, 0.5).
        field: one of 'credit', 'lwp', 'debit'. Default 'debit' (leave taken).
    Returns a confirmation string."""
    sheet = get_sheet()
    date = sheet.resolve_month(month)   # loose month -> stored row key
    sheet.add_leave(name, date, days, field)
    new_val = sheet.get_employee(name)["leaves"][date][field]
    return f"Added {days} to {field} for {name} on {date}. New {field}={new_val}."


def get_tools() -> list:
    """All leave-sheet tools, ready to pass to llm.bind_tools(...)."""
    return [list_employees, get_employee_leaves, get_leave_balance, record_leave]
