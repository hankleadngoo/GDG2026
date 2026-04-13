# Unit Testing Rules

## Framework

Use **`pytest`** for all backend unit tests. Do not use `unittest` directly.

## File & Directory Convention

- Place all tests under `backend/tests/`
- Mirror the source structure: a test for `backend/agents/agent1_extractor/parser.py` lives at `backend/tests/agents/agent1_extractor/test_parser.py`
- Every test file must be prefixed with `test_`
- Every test function must be prefixed with `test_`

```
backend/
└── tests/
    ├── __init__.py
    ├── agents/
    │   ├── agent1_extractor/
    │   │   └── test_parser.py
    │   ├── agent2_osint/
    │   │   └── test_searcher.py
    │   ├── agent3_verifier/
    │   │   └── test_checker.py
    │   ├── agent4_rag/
    │   │   └── test_retriever.py
    │   └── agent5_synthesizer/
    │       └── test_reporter.py
    ├── api/
    │   └── test_routes.py
    └── workflow/
        └── test_graph.py
```

## Running Tests

```bash
# All tests
pytest backend/tests/

# Single file
pytest backend/tests/agents/agent1_extractor/test_parser.py

# Single test function
pytest backend/tests/agents/agent1_extractor/test_parser.py::test_extracts_linkedin_url

# With output (no capture)
pytest -s backend/tests/

# With coverage report
pytest --cov=backend --cov-report=term-missing backend/tests/
```

## Mocking External APIs

All external API calls **must** be mocked in unit tests. Never make real network calls in tests.

Use `pytest-mock` (`mocker` fixture) or `unittest.mock.patch`:

```python
# Mock Gemini API call
def test_parser_structures_profile(mocker):
    mocker.patch("agents.agent1_extractor.parser.call_gemma", return_value={...})
    ...

# Mock Tavily search
def test_searcher_handles_empty_results(mocker):
    mocker.patch("agents.agent2_osint.searcher.tavily_client.search", return_value=[])
    ...
```

Mock targets to patch for each agent:

| Agent | Mock Target |
|-------|------------|
| Agent 1 | `call_gemma`, `pymupdf.open` / `llama_parse` |
| Agent 2 | `tavily_client.search`, `proxycurl.get`, `github.Github` |
| Agent 3 | `genai.GenerativeModel.generate_content`, `gmail_api.send` |
| Agent 4 | `faiss.IndexFlatL2.search`, `genai.embed_content` |
| Agent 5 | `genai.GenerativeModel.generate_content` |

## Test Fixtures

Define shared fixtures in `backend/tests/conftest.py`:

```python
# conftest.py
import pytest

@pytest.fixture
def sample_cv_text():
    return """John Doe\nSoftware Engineer\nGitHub: github.com/johndoe\n..."""

@pytest.fixture
def sample_candidate_profile():
    return {
        "name": "John Doe",
        "skills": ["Python", "FastAPI"],
        "links": ["https://github.com/johndoe"],
        ...
    }
```

## What to Test per Agent

### Agent 1 — Extractor
- Correctly parses name, email, skills, experience from raw text
- Extracts and classifies URLs (LinkedIn vs GitHub vs other)
- Handles empty / malformed CV gracefully (returns partial profile, no exception)

### Agent 2 — OSINT
- Returns `osint_status = "skipped"` when no links are provided
- Returns `osint_status = "partial"` when one source fails
- Filters out irrelevant search results

### Agent 3 — Verifier
- Detects contradictions when CV claim differs from OSINT data
- Sets `trust_score < 0.5` on significant contradictions
- Does NOT crash when `osint_data` is empty (CV-only verification path)

### Agent 4 — RAG Retriever
- Returns empty benchmark with warning when no similar CVs found
- Aggregates skill frequencies correctly across retrieved profiles

### Agent 5 — Synthesizer
- Produces all required `final_report` fields
- Populates `pipeline_warnings` when inputs are incomplete

### API Routes
- `POST /evaluate` returns 200 with a `job_id`
- `GET /report/{job_id}` returns 404 for unknown IDs
- `POST /feedback/{job_id}` stores decision without error

## Required `pytest` Plugins

Add to `backend/requirements.txt`:
```
pytest
pytest-mock
pytest-asyncio
pytest-cov
httpx              # for FastAPI async test client
```

Use `@pytest.mark.asyncio` for any async agent or route tests.
