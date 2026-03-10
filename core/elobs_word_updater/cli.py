from __future__ import annotations
import asyncio
import sys
from pathlib import Path
import click
from .config import load_config
from .auth.factory import create_auth_client
from .api.client import StudyApiClient
from .updater import update_document


@click.command()
@click.version_option(None, "--app-version", package_name="elobs-word-updater", prog_name="elobs-word-updater")
@click.option("--study", required=True, help="Study UID (e.g. Study_000001)")
@click.option("--version", default=None, help="Study version number (e.g. 1). Omit for LATEST.")
@click.option("--template", required=True, type=click.Path(exists=True), help="Path to input .docx template")
@click.option("--out", required=True, help="Path to write the updated .docx")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
@click.option("--api", default=None, help="Override API base URL from config")
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Limit update to specific SB_ tags (repeatable). Omit to update all.",
)
def main(
    study: str,
    version: str | None,
    template: str,
    out: str,
    config_path: str | None,
    api: str | None,
    tags: tuple[str, ...],
) -> None:
    """Update SB_* content controls in a Word document from OpenStudyBuilder API."""
    cfg = load_config(config_path)
    if api:
        cfg.api.url = api

    auth_client = create_auth_client(cfg.api.url, cfg.api.auth)
    api_client = StudyApiClient(auth_client)

    result = asyncio.run(
        update_document(
            doc_path=template,
            output_path=out,
            study_uid=study,
            version=version or None,
            api_client=api_client,
            tags=list(tags) if tags else None,
        )
    )

    click.echo(f"Updated : {len(result.updated)} fields -> {out}")
    if result.skipped:
        click.echo(f"Skipped : {', '.join(result.skipped)} (no API data)")
    if result.missing:
        click.echo(f"Missing : {', '.join(result.missing)} (not in template)")
    if result.api_errors:
        click.echo(f"API errors: {', '.join(result.api_errors)} (see warnings above)")

    sys.exit(0)
