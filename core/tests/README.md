# Tests

## Setup

Install the package with dev dependencies:

```bash
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Running Tests

Run all tests from the project root:

```bash
pytest
```

Run a specific test file:

```bash
pytest tests/test_integration.py
pytest tests/test_cli.py
pytest tests/test_api_client.py
pytest tests/test_content_controls.py
pytest tests/test_merger.py
pytest tests/test_properties.py
pytest tests/test_svg_embedder.py
```

Run with verbose output:

```bash
pytest -v
```

Generate an HTML report with test titles and descriptions (saved to `tests/report.html`):

```bash
pytest --html=tests/report.html --self-contained-html -v
```

The `-v` flag enables verbose mode, which causes each test's docstring to appear as its description in the report. Open `tests/report.html` in any browser to view the results.

## Test Structure

| File | What it tests |
|------|--------------|
| `test_integration.py` | End-to-end document update using the full pipeline |
| `test_cli.py` | CLI entry point (`elobs-word-updater`) |
| `test_api_client.py` | `StudyApiClient` against the dummy API |
| `test_content_controls.py` | Word content control parsing and manipulation |
| `test_merger.py` | Document merge/compose logic |
| `test_properties.py` | Document property extraction |
| `test_svg_embedder.py` | SVG embedding into Word documents |

## Dummy API Server

Tests that make HTTP calls use a local dummy API server defined in `dummy_api/app.py`. It is started automatically by the `dummy_api_server` session-scoped pytest fixture in `conftest.py` and serves fixture data from the `fixtures/` directory on `http://127.0.0.1:18765`. No manual setup is required.

## Fixtures

Static test data lives in `fixtures/`. This includes sample JSON payloads from the OpenStudyBuilder API and `.docx`/`.svg` files used as inputs and expected outputs.
