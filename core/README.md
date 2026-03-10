# elobs-word-updater — Core

A Python CLI tool that fetches data from the [OpenStudyBuilder](https://openstudybuilder.com) API and updates `SB_*` content controls and custom document properties in a Word (`.docx`) template.

Designed to run as a script or background task — no Microsoft 365 or Office installation required.

This package is also the dependency used by the [OSB API extension](../osb-api-extension/README.md).

## Features

- Updates all `SB_*` tagged content controls in a Word template
- Inserts sub-documents (flowchart, objectives) via full DOCX merging
- Embeds SVG study design graphics as native Word SVG (Word 2016+)
- Updates custom document properties (StudyUID, StudyVersion, etc.)
- Supports specific study versions (`--version 1`) or LATEST (default)
- Authentication: no-auth (default) — OAuth 2.0 placeholder ready

## Installation

**Linux / macOS / PowerShell:**
```bash
pip install -e ".[dev]"
```

**Windows PowerShell** — if you get a `PermissionError` related to `SSLKEYLOGFILE`, clear it first:
```powershell
$env:SSLKEYLOGFILE = $null
pip install -e .
```

**Windows CMD** — if you get a `PermissionError` related to `SSLKEYLOGFILE`, clear it first:
```cmd
set SSLKEYLOGFILE=
pip install -e .
```

## Usage

### Linux / macOS / PowerShell

```bash
# Update all fields, latest version, no auth
elobs-word-updater \
  --study Study_000001 \
  --template .\templates\ProtocolTemplate_OSB_1.1.docx \
  --out my_protocol_output.docx \
  --api http://localhost:5005/api

# Specific version
elobs-word-updater \
  --study Study_000001 \
  --version 1 \
  --template .\templates\ProtocolTemplate_OSB_1.1.docx \
  --out output.docx

# Only specific fields
elobs-word-updater \
  --study Study_000001 \
  --template .\templates\ProtocolTemplate_OSB_1.1.docx \
  --out output.docx \
  --tag SB_ProtocolTitle \
  --tag SB_StudyID
```

### Windows CMD

Use `^` for line continuation instead of `\`:

```cmd
REM Update all fields, latest version, no auth
elobs-word-updater ^
  --study Study_000001 ^
  --template .\templates\ProtocolTemplate_OSB_1.1.docx ^
  --out my_protocol_output.docx ^
  --api http://localhost:5005/api

REM Specific version
elobs-word-updater ^
  --study Study_000001 ^
  --version 1 ^
  --template .\templates\ProtocolTemplate_OSB_1.1.docx ^
  --out output.docx

REM Only specific fields
elobs-word-updater ^
  --study Study_000001 ^
  --template .\templates\ProtocolTemplate_OSB_1.1.docx ^
  --out output.docx ^
  --tag SB_ProtocolTitle ^
  --tag SB_StudyID
```

Or put everything on one line:

```cmd
elobs-word-updater --study Study_000001 --template .\templates\ProtocolTemplate_OSB_1.1.docx --out my_protocol_output.docx --api http://localhost:5005/api
```

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit:

```yaml
api:
  url: http://localhost:5005/api
  auth:
    type: none   # "oauth" coming in a future version
```

## Content Controls

Place content controls with the following tags in your Word template:

| Tag | Content |
|-----|---------|
| `SB_ProtocolTitle` | Protocol title |
| `SB_ProtocolTitleShort` | Short title |
| `SB_Acronym` | Study acronym |
| `SB_Substance` | Drug/substance name |
| `SB_StudyID` | Study ID |
| `SB_StudyPhase` | Trial phase |
| `SB_EudraCTNumber` | EudraCT number |
| `SB_INDNumber` | IND number |
| `SB_UniversalTrialNumber` | UTN |
| `SB_EUTrialNumber` | EU trial number |
| `SB_NCT` | ClinicalTrials.gov ID |
| `SB_jRCT` | Japanese registry number |
| `SB_NMPA` | China NMPA number |
| `SB_EUDAMED` | EUDAMED number |
| `SB_IDE` | IDE number |
| `SB_CIVID_SIN` | CIV-ID / SIN number |
| `SB_InclusionCriteria` | Inclusion criteria (one per paragraph) |
| `SB_ExclusionCriteria` | Exclusion criteria (one per paragraph) |
| `SB_ObjectivesEndpoints` | Objectives & endpoints (DOCX merged) |
| `SB_Flowchart` / `SB_SoA` | Schedule of Activities (DOCX merged) |
| `SB_StudydesignGraphic` | Study design diagram (SVG) |

## Custom Document Properties

In addition to content controls, the tool writes custom properties to the output document (visible in Word under *File → Info → Properties → Advanced Properties → Custom*):

| Property | Value |
|---|---|
| `StudyUID` | The study UID passed via `--study` (e.g. `Study_000001`) |
| `StudyId` | The study ID from the API identification metadata |
| `StudyVersion` | The requested version number, or `LATEST` when `--version` is omitted |
| `StudyVersionStatus` | The study status returned by the API (e.g. `DRAFT`, `RELEASED`) |
| `OSBSyncedAt` | UTC timestamp of the synchronization run (e.g. `2026-03-07T11:23:45Z`) |

These properties are only written if the template already contains a `docProps/custom.xml` part. A blank `Document()` created by python-docx does not have this part; use a Word template that was saved with at least one custom property.

## Running Tests

```bash
pytest
```

Generate an HTML report with test titles and descriptions (saved to `tests/report.html`):

```bash
pytest --html=tests/report.html --self-contained-html -v
```

Tests use a local dummy API (FastAPI) that serves fixture data — no running OpenStudyBuilder instance required.

To refresh test fixtures from a running API:

```bash
python scripts/fetch_fixtures.py --api http://localhost:5005/api --study Study_000001
```

## Roadmap

- [ ] OAuth 2.0 authentication (generic, supports Azure AD / Keycloak / Auth0)
- [ ] Watch mode (re-run when template changes)
