"""
agent5_evaluator — The Final Evaluator agent package.

Public API
----------
run_agent5(state)  →  dict
    Called at the very end of the pipeline. It consumes data from Agent 1 (CV),
    Agent 3 (Trust Score), and Agent 4 (Benchmark) to formulate a final hiring
    decision, infer hidden strengths/weaknesses, and draft feedback emails.
"""

from .evaluator import run_agent5

__all__ = ["run_agent5"]