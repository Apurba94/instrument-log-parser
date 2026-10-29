"""Parse raw instrument logs into tidy CSV using configurable regex rules."""
from .core import Parser, load_config

__version__ = "0.1.0"
__all__ = ["Parser", "load_config"]
