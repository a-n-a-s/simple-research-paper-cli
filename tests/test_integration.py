import csv
import json

import httpx
import pytest
import respx

# from researchhub import main as main_module
import researchhub.main as main_module
from researchhub.main import run
from researchhub.models import Paper


ARXIV_URL = "https://export.arxiv.org/api/query"
CROSSREF_URL = "https://api.crossref.org/works"


def _mock_both(arxiv_xml: bytes, crossref_json: dict):
    respx.get(ARXIV_URL).mock(
        return_value=httpx.Response(200, content=arxiv_xml)
    )
    respx.get(CROSSREF_URL).mock(
        return_value=httpx.Response(200, json=crossref_json)
    )


def _feed_inputs(monkeypatch, values: list[str]):
    it = iter(values)
    monkeypatch.setattr("builtins.input", lambda *_: next(it))


@respx.mock
async def test_happy_path_json(monkeypatch, tmp_path, arxiv_xml, crossref_json):
    _mock_both(arxiv_xml, crossref_json)
    out = tmp_path / "out.json"
    _feed_inputs(monkeypatch, ["json", str(out)])

    await run("attention", 5)

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    # 3 arXiv + 3 Crossref - 1 deduped - 1 empty-title skipped = 4
    assert len(data) == 4
    for row in data:
        assert set(row) == {
            "paper_id", "title", "authors", "abstract",
            "doi", "publication_year", "source", "paper_url",
        }
        assert isinstance(row["paper_id"], str)
        assert isinstance(row["authors"], list)


@respx.mock
async def test_happy_path_csv(monkeypatch, tmp_path, arxiv_xml, crossref_json):
    _mock_both(arxiv_xml, crossref_json)
    out = tmp_path / "out.csv"
    _feed_inputs(monkeypatch, ["csv", str(out)])

    await run("attention", 5)

    assert out.exists()
    with out.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    # authors are "; "-joined strings in CSV, never lists
    for row in rows:
        assert isinstance(row["authors"], str)
    assert any("; " in r["authors"] for r in rows)


@respx.mock
async def test_dedup_across_sources_arxiv_wins(
    monkeypatch, tmp_path, arxiv_xml, crossref_json
):
    _mock_both(arxiv_xml, crossref_json)
    out = tmp_path / "out.json"
    _feed_inputs(monkeypatch, ["json", str(out)])

    await run("attention", 5)

    data = json.loads(out.read_text(encoding="utf-8"))
    dupes = [r for r in data if r["title"] == "Duplicate Title For Dedup Test"]
    assert len(dupes) == 1
    assert dupes[0]["source"] == "arxiv"


@respx.mock
async def test_one_source_fails_other_still_exports(
    monkeypatch, tmp_path, crossref_json, caplog
):
    respx.get(ARXIV_URL).mock(return_value=httpx.Response(500))
    respx.get(CROSSREF_URL).mock(
        return_value=httpx.Response(200, json=crossref_json)
    )
    out = tmp_path / "out.json"
    _feed_inputs(monkeypatch, ["json", str(out)])

    with caplog.at_level("WARNING"):
        await run("attention", 5)

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    # Crossref only: 3 items, one with empty title skipped → 2
    assert len(data) == 2
    assert all(r["source"] == "crossref" for r in data)
    assert any("arXiv" in rec.message for rec in caplog.records)


@respx.mock
async def test_both_sources_fail(monkeypatch, tmp_path, caplog):
    respx.get(ARXIV_URL).mock(return_value=httpx.Response(500))
    respx.get(CROSSREF_URL).mock(return_value=httpx.Response(500))
    out = tmp_path / "out.json"
    _feed_inputs(monkeypatch, ["json", str(out)])

    with caplog.at_level("WARNING"):
        await run("attention", 5)

    # nothing to export → no file, or empty per your contract; assert no crash
    assert not out.exists() or out.read_text() in ("", "[]")
    assert any("arXiv" in r.message for r in caplog.records)
    assert any("Crossref" in r.message for r in caplog.records)


@respx.mock
def test_bad_input_makes_no_network_call(monkeypatch, caplog):
    _feed_inputs(monkeypatch, [""])

    with pytest.raises(SystemExit):
        main_module.main()

    assert respx.calls.call_count == 0


@respx.mock
async def test_bad_format_skips_export(
    monkeypatch, tmp_path, arxiv_xml, crossref_json
):
    _mock_both(arxiv_xml, crossref_json)
    out = tmp_path / "out.xml"
    _feed_inputs(monkeypatch, ["xml", str(out)])

    await run("attention", 5)

    assert not out.exists()


@respx.mock
def test_main_full_cli_flow(
    monkeypatch, tmp_path, arxiv_xml, crossref_json
):
    _mock_both(arxiv_xml, crossref_json)
    out = tmp_path / "cli.json"
    _feed_inputs(monkeypatch, ["attention", "5", "json", str(out)])

    main_module.main()

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 4