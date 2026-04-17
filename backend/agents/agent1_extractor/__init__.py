"""
agent1_extractor — CV Parsing and Extraction agent package.

Public API
----------
parse_cv(source, job_description)  →  dict
    Extracts structured data from a single PDF/DOCX or text string.
    Returns a dict matching the CVExtraction dataclass schema.
    
main_pipeline(input_dir, output_json_file)  →  None
    Batch processes a directory of CVs asynchronously to build a database.
"""

from .parser import parse_cv
from .extract import main_pipeline

__all__ = ["parse_cv", "main_pipeline"]