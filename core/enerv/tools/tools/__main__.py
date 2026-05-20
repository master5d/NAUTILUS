"""Entry point for tools CLI module."""
import sys
from tools.tools.cli import facet

if __name__ == "__main__":
    # When invoked as python -m tools.tools, invoke the facet click group
    facet()
