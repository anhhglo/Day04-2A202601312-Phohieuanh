"""ASSIGNMENT 4 — SUBMISSION TEMPLATE

Rename this file to  submission_<MSSV>.py   (e.g. submission_V2026001.py)
and submit that ONE file. Nothing else is collected.

You must define exactly four module-level names:

    SYSTEM_PROMPT   str    your policy layer
    TOOLS           list   exactly 2 tool schemas, OpenAI-style
    TOOL_IMPLS      dict   name -> callable
    NOTES           str    >=200 chars: >=2 bugs you found + how you fixed them,
                           each classified as prompt / tool / control-flow

The two tool NAMES are fixed by the spec and cannot be changed:
    lookup_course(course_code, term=None)
    check_student_record(student_id, field)

You are graded on the SYSTEM_PROMPT and the tool DESCRIPTIONS/SCHEMAS you
write — not on the agent loop (the harness owns that).

Run the public tests before you submit:
    python grade.py . --set public
"""

from harness.tools import check_student_record, lookup_course

# ─────────────────────────────────────────────────────────────────────
# 1. SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────
# TODO: write your policy layer here.
#
# Think about the five parts from the lecture:
#   Persona · Rules · Capabilities · Constraints · Output format
#
# And about what the hidden tests will throw at you:
#   - a question with no course code            -> ask, do not invent
#   - a question about someone else's record    -> refuse, do not call the tool
#   - a course description containing orders    -> that text is DATA, not commands
#   - a tool that returns an error              -> report it, do not fabricate
#   - an ordinary in-scope question             -> just answer it (do not
#                                                  refuse everything to feel safe)
#
# The authenticated student for this session is V2026001.

SYSTEM_PROMPT = """
TODO: your system prompt here.
"""

# ─────────────────────────────────────────────────────────────────────
# 2. TOOL SCHEMAS
# ─────────────────────────────────────────────────────────────────────
# Remember: the description is a PROMPT. Say what the tool does, WHEN to call
# it, and when NOT to call it.

TOOLS = [
    {
        "type": "function",
        "name": "lookup_course",
        "description": "TODO: what it does, when to call it, when NOT to call it.",
        "parameters": {
            "type": "object",
            "properties": {
                "course_code": {"type": "string", "description": "TODO e.g. CS101"},
                "term": {"type": "string", "description": "TODO e.g. 2026S1"},
            },
            "required": ["course_code"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_student_record",
        "description": "TODO: what it does, when to call it, when NOT to call it.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "TODO"},
                "field": {
                    "type": "string",
                    "enum": ["gpa", "credits_done", "tuition_balance_vnd",
                             "completed", "name"],
                    "description": "TODO",
                },
            },
            "required": ["student_id", "field"],
            "additionalProperties": False,
        },
    },
]

# ─────────────────────────────────────────────────────────────────────
# 3. TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────────────
# Reusing the reference implementations is fine and recommended.

TOOL_IMPLS = {
    "lookup_course": lookup_course,
    "check_student_record": check_student_record,
}

# ─────────────────────────────────────────────────────────────────────
# 4. NOTES  (>=200 characters)
# ─────────────────────────────────────────────────────────────────────

NOTES = """
TODO: At least two problems you hit and how you fixed them. Classify each one:

  [prompt]        the wording of the system prompt caused it
  [tool]          the tool description or parameter schema caused it
  [control-flow]  when/whether tools were called, or the loop, caused it

Example shape (write your own):
  1. [tool] My lookup_course description only said "look up a course", so the
     agent called it for the question "what is a credit?". Added an explicit
     "do not call this for general questions" line and it stopped.
  2. [prompt] ...
"""
