#!/usr/bin/env python
"""Build the separate GAIB-1 exit-criteria candidate notebook."""

from __future__ import annotations

import os


os.environ["GAIB_EXIT_CRITERIA_NOTEBOOK_NAME"] = "Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb"

from build_token_root_cause_experiment import main


if __name__ == "__main__":
    main()
