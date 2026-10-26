"""Validate a directory against Writing Room layout v1 (docs/LAYOUT_V1.md).

    python tools/check_layout_v1.py [ROOT]      # default: fixtures/legacy-v1

Exit 0 if the project is a valid layout-v1 root, 1 otherwise. Thin wrapper over
skills/writing-room/scripts/wr_layout.py, which is also what wr_doctor uses.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "writing-room" / "scripts"))

from wr_layout import check  # noqa: E402


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "fixtures" / "legacy-v1"
    errors, warnings = check(root, coverage=True)
    for w in warnings:
        print(f"warn   {w}")
    for e in errors:
        print(f"ERROR  {e}")
    print(f"{root}: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
