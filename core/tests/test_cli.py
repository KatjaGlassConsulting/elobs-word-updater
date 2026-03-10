from __future__ import annotations
import io
from pathlib import Path
from docx import Document
from lxml import etree
from click.testing import CliRunner
from elobs_word_updater.cli import main
from tests.conftest import DUMMY_API_URL

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _make_template(tmp_path: Path, tags: list[str]) -> str:
    doc = Document()
    for tag in tags:
        xml = f"""
<w:sdt xmlns:w="{W_NS}">
  <w:sdtPr><w:tag w:val="{tag}"/></w:sdtPr>
  <w:sdtContent><w:p><w:r><w:t>PLACEHOLDER</w:t></w:r></w:p></w:sdtContent>
</w:sdt>""".strip()
        doc.element.body.append(etree.fromstring(xml))
    path = tmp_path / "template.docx"
    doc.save(str(path))
    return str(path)


def test_cli_help():
    """Help output lists --study, --template, and --out flags."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--study" in result.output
    assert "--template" in result.output
    assert "--out" in result.output


def test_cli_missing_required_args():
    """Invoking the CLI with no arguments exits with a non-zero code."""
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0


def test_cli_missing_study():
    """Invoking without --study exits with a non-zero code."""
    runner = CliRunner()
    result = runner.invoke(main, ["--template", "x.docx", "--out", "out.docx"])
    assert result.exit_code != 0


def test_cli_full_run(dummy_api_server, tmp_path):
    """Full CLI run against dummy API updates content controls and writes the output file."""
    template = _make_template(tmp_path, ["SB_ProtocolTitle", "SB_StudyID"])
    out = str(tmp_path / "output.docx")
    runner = CliRunner()
    result = runner.invoke(main, [
        "--study", "Study_000001",
        "--template", template,
        "--out", out,
        "--api", DUMMY_API_URL,
    ])
    assert result.exit_code == 0
    assert "Updated" in result.output
    assert Path(out).exists()


def test_cli_specific_tag(dummy_api_server, tmp_path):
    """--tag flag limits updates to only the specified content control."""
    template = _make_template(tmp_path, ["SB_ProtocolTitle", "SB_StudyID"])
    out = str(tmp_path / "output.docx")
    runner = CliRunner()
    result = runner.invoke(main, [
        "--study", "Study_000001",
        "--template", template,
        "--out", out,
        "--api", DUMMY_API_URL,
        "--tag", "SB_ProtocolTitle",
    ])
    assert result.exit_code == 0
    assert "Updated" in result.output


def test_cli_reports_missing_tags(dummy_api_server, tmp_path):
    """Tags requested but not in template appear in Missing output."""
    template = _make_template(tmp_path, ["SB_ProtocolTitle"])
    out = str(tmp_path / "output.docx")
    runner = CliRunner()
    result = runner.invoke(main, [
        "--study", "Study_000001",
        "--template", template,
        "--out", out,
        "--api", DUMMY_API_URL,
        "--tag", "SB_ProtocolTitle",
        "--tag", "SB_StudyID",
    ])
    assert result.exit_code == 0
    assert "Missing" in result.output


def test_cli_version_flag(dummy_api_server, tmp_path):
    """--version flag selects historic version from API."""
    template = _make_template(tmp_path, ["SB_ProtocolTitle"])
    out = str(tmp_path / "output.docx")
    runner = CliRunner()
    result = runner.invoke(main, [
        "--study", "Study_000001",
        "--version", "1",
        "--template", template,
        "--out", out,
        "--api", DUMMY_API_URL,
    ])
    assert result.exit_code == 0
    doc = Document(out)
    texts = " ".join(t.text for t in doc.element.body.iter(f"{{{W_NS}}}t") if t.text)
    assert "(new)" not in texts
