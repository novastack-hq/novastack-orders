"""One place to configure logging for the CLI and scripts."""

from __future__ import annotations

import logging

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging(level: str = "WARNING") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.WARNING), format=FORMAT
    )
