"""Allow ``python -m openayane_rde.cli``."""

from __future__ import annotations

import sys

from openayane_rde.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
