# elobs-word-updater — OSB Frontend Extension

A Vue.js extension for [OpenStudyBuilder](https://openstudybuilder.com) that adds a **ELOBS Word Updater** page under Studies. Users can select a study, choose a version, pick which fields to populate, upload a Word template, and download the result — all from within the OpenStudyBuilder UI.

Requires the [OSB API extension](../osb-api-extension/README.md) to be installed and running.

## Prerequisites

- OpenStudyBuilder frontend (studybuilder)
- OSB API extension installed and running on port 8009

## Installation

Copy the `elobs-word-updater/` folder into the StudyBuilder extensions directory:

```
studybuilder/src/extensions/elobs-word-updater/
```

The extension is loaded automatically when the StudyBuilder development server starts or the application is built.

The ELOBS Word Updater page will appear in the **Studies** sidebar menu.

## Development

Start the StudyBuilder development server from the `studybuilder/` directory:

```bash
yarn dev
```

The extension will be available at:

```
http://localhost:5173/studies/elobs-word-updater
```

Run code quality checks:

```bash
yarn format
yarn lint
```
