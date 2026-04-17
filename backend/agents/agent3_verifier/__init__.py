"""
agent3_verifier — Trust Score & Cross-Verification agent package.

Public API
----------
run_agent3(state)  →  dict
    Called after Agent 1 and Agent 2 finish. Consumes parsed CV data and OSINT
    crawled data to cross-reference claims, calculate a trust score, and flag
    any inconsistencies or missing evidence.
"""

from .verifier import run_agent3

__all__ = ["run_agent3"]