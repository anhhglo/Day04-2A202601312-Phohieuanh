"""Static safety check applied to a submission BEFORE it is imported.

Why this exists
---------------
`grade.py` imports each submission with `exec_module`, which runs arbitrary
student code inside the grader process. In a 500-student cohort that is a real
exposure, and not only to malice — one careless `while True:` or a stray
`open(...)` in the wrong mode can wreck a grading run. A submission could also
simply read `tests/hidden.json` and hard-code the answers.

This is a static AST screen, not a sandbox. It raises the cost of the obvious
attacks and produces an auditable reason string; it is not a security boundary.
For a graded run where that matters, also run the grader as an unprivileged
user in a throwaway directory with the hidden tests mounted read-only
elsewhere.
"""

import ast

ALLOWED_IMPORTS = {
    "harness", "harness.tools", "harness.data",
    "json", "re", "typing", "dataclasses", "textwrap", "math",
    "sys", "pathlib",          # the template uses these two for sys.path setup
}

BANNED_NAMES = {
    "eval", "exec", "compile", "__import__", "open", "input",
    "globals", "locals", "vars", "getattr", "setattr", "delattr",
    "memoryview", "breakpoint",
}

BANNED_MODULES = {
    "os", "subprocess", "shutil", "socket", "requests", "urllib", "http",
    "importlib", "ctypes", "multiprocessing", "threading", "pickle", "shelve",
    "builtins", "gc", "inspect", "gzip", "tempfile", "sqlite3", "gettext",
}

# Note: ".." was deliberately REMOVED from this list. It matched the ellipsis
# in a perfectly ordinary output contract — {"intent": "..."} — and would have
# rejected legitimate submissions.
# "grade.py" and "results.csv" were also removed: the submission template's own
# docstring tells students to run `python grade.py`, so those strings appear in
# every legitimate submission. Reading either file requires `open`, which is
# banned outright above — the string check adds nothing but false positives.
SUSPICIOUS_STRINGS = ("hidden.json", "tests/", "__pycache__", "/etc/",
                      "os.system", "subprocess")


def _module_root(name):
    return (name or "").split(".")[0]


def check_source(src: str):
    """Return a list of reasons this submission must not be imported."""
    problems = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"syntax error: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = _module_root(a.name)
                if a.name not in ALLOWED_IMPORTS and root not in ALLOWED_IMPORTS:
                    problems.append(f"import of '{a.name}' is not allowed")
                if root in BANNED_MODULES:
                    problems.append(f"banned module '{a.name}'")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = _module_root(mod)
            if mod not in ALLOWED_IMPORTS and root not in ALLOWED_IMPORTS:
                problems.append(f"import from '{mod}' is not allowed")
            if root in BANNED_MODULES:
                problems.append(f"banned module '{mod}'")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            problems.append(f"use of '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            problems.append(f"dunder attribute access '{node.attr}'")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            # no length exemption: a long docstring is exactly where you would
            # hide a path you intend to read
            for s in SUSPICIOUS_STRINGS:
                if s in low:
                    problems.append(f"suspicious string literal {node.value[:40]!r}")
                    break
        elif isinstance(node, (ast.While, ast.AsyncFor)):
            problems.append("while loops are not allowed in a submission")

    # de-duplicate, keep order
    seen, out = set(), []
    for p in problems:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out[:6]
