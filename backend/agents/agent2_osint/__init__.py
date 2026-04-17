"""
agent2_osint — Open Source Intelligence (OSINT) agent package.

Public API
----------
run_agent2(state)  →  dict
    Called after Agent 1 finishes. Iterates through the extracted URLs (GitHub,
    Portfolio, etc.), crawls the public data, and uses AI to summarize expertise 
    (e.g., analyzing GitHub READMEs). Writes the gathered OSINT data back to the state.
"""

from .osint import run_agent2

__all__ = ["run_agent2"]