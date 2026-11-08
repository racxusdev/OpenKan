#!/usr/bin/env python3
"""Executa o OpenKan direto do código-fonte (sem instalar).

Uso:
    python3 run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openkan.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
