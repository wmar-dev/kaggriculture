"""Bundle `src/kaggriculture_agent/` into a single self-contained Kaggle
submission file (research.md R2): one `main.py` with no local imports,
matching what `kaggle competitions submit` expects (AGENTS.md).

Also guards against the exact bug this project hit during development:
`kaggle_environments`' file loader picks the LAST callable defined in the
file as the agent, not whichever one is named `agent` (see the docstring
in src/kaggriculture_agent/agent.py). `main()` refuses to write a bundle
where that isn't true.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "src" / "kaggriculture_agent"

# Dependency order matters: each later module may use names defined by an
# earlier one, and `agent.py` MUST be last so `agent()` stays the last
# callable in the bundled file.
MODULE_ORDER = ["constants.py", "observation.py", "strategy.py", "agent.py"]

_FUTURE_IMPORT_RE = re.compile(r"^from __future__ import annotations\s*$", re.MULTILINE)
_LOCAL_IMPORT_RE = re.compile(r"^from kaggriculture_agent\.\w+ import .+$", re.MULTILINE)


def _strip_module(source: str) -> str:
    source = _FUTURE_IMPORT_RE.sub("", source)
    source = _LOCAL_IMPORT_RE.sub("", source)
    return source.strip("\n")


def build_bundle() -> str:
    parts = ["from __future__ import annotations", ""]
    for name in MODULE_ORDER:
        path = PACKAGE_DIR / name
        parts.append(f"# ---- {name} " + "-" * max(0, 60 - len(name)))
        parts.append(_strip_module(path.read_text()))
        parts.append("")
    return "\n".join(parts) + "\n"


def _last_callable_name(source: str) -> str | None:
    """Mirror kaggle_environments' `get_last_callable`: exec the bundle in
    a fresh namespace and return the name of the last callable defined."""
    namespace: dict = {}
    exec(compile(source, "<bundle>", "exec"), namespace)
    callables = [k for k, v in namespace.items() if callable(v) and not k.startswith("__")]
    return callables[-1] if callables else None


def write_bundle(out_path: Path) -> None:
    source = build_bundle()
    ast.parse(source)  # fail fast on a syntax error before checking semantics
    last = _last_callable_name(source)
    if last != "agent":
        raise RuntimeError(
            f"Refusing to write bundle: last callable in the file is "
            f"{last!r}, not 'agent'. kaggle_environments would silently "
            f"load the wrong function (see this file's module docstring)."
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(source)


def _next_version_dir() -> Path:
    existing = [p for p in (REPO_ROOT / "submissions").glob("v*") if p.is_dir()]
    numbers = [int(p.name[1:]) for p in existing if p.name[1:].isdigit()]
    return REPO_ROOT / "submissions" / f"v{max(numbers, default=0) + 1}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="Output path, e.g. submissions/v1/main.py (default: next submissions/vN/main.py)")
    args = parser.parse_args(argv)

    out_path = (Path(args.out) if args.out else (_next_version_dir() / "main.py")).resolve()
    write_bundle(out_path)
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
