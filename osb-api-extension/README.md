# elobs-word-updater — OSB API Extension

A backend extension for [OpenStudyBuilder](https://openstudybuilder.com) that exposes a single endpoint for generating populated Word documents from within the OSB platform.

Accepts a Word template and study parameters, runs the `elobs-word-updater` core package internally, and returns the updated `.docx` as a file download. Authentication is handled by OSB's existing middleware — no separate auth configuration required.

The extension calls OSB's internal service layer directly (in-process), so no HTTP requests are made to the OSB API and no `OSB_API_URL` environment variable is needed.

## Prerequisites

- OpenStudyBuilder with the extensions API enabled (running on port 8009 by default)
- Python environment for the extensions API

## Installation

### 1. Install the core package

In OSB's Python environment (where the extensions API runs):

```bash
pip install elobs-word-updater
```

For local development against this repo:

```bash
pip install -e ../core/
```

### 2. Copy the extension

Copy the `elobs_word_updater_ext/` folder into OpenStudyBuilder's extensions directory:

```
clinical-mdr-api/extensions/elobs_word_updater_ext/
```

### 3. Restart the extensions API

```bash
pipenv run extensions-api-dev
```

The extension is loaded automatically. The endpoint will be available at:

```
http://localhost:8009/elobs-word-updater/generate
```

## Docker setup

For local development with Docker Compose, copy the `elobs_word_updater_ext/` folder into `clinical-mdr-api/extensions/` (step 2 above), then add the following to your OSB project's `compose.override.yaml` to install the `core` package into the container:

```yaml
services:
  extensionsapi:
    volumes:
      - /path/to/elobs-word-updater/core:/tmp/elobs-core:ro
    command: >-
      sh -c "pipenv run pip install --quiet /tmp/elobs-core && exec pipenv run uvicorn"
```

> Replace `/path/to/elobs-word-updater` with the path where you cloned this repo.

> Once `elobs-word-updater` is published to PyPI, the `compose.override.yaml` is no longer needed — replace it with a plain `pip install elobs-word-updater` in the container.

## API

### `POST /elobs-word-updater/generate`

Generates a populated Word document for the given study.

**Request** — `multipart/form-data`:

| Field | Type | Required | Description |
|---|---|---|---|
| `template` | file (`.docx`) | Yes | Word template containing `SB_*` content controls |
| `study_uid` | string | Yes | OpenStudyBuilder study UID (e.g. `Study_000001`) |
| `version` | string | No | Study version number. Omit for latest. |
| `tags` | string[] | No | Specific `SB_*` tags to update. Omit to update all. |

**Response** — `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

The populated `.docx` file as a download.

## Running Extension Tests

From the OpenStudyBuilder `clinical-mdr-api/` directory:

```bash
pipenv run extensions-test
```
