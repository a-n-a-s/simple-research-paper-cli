import csv
import json
import uuid

import pytest

from researchhub.export import export, export_csv, export_json


def test_export_json_roundtrips_uuid_as_str(make_paper, tmp_path):
    p = make_paper(paper_id=uuid.uuid4(), title="Ünïcode Tïtle", authors=["Äda Lovelace"])
    out = tmp_path / "p.json"
    export_json([p], str(out))
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data[0]["paper_id"] == str(p.paper_id)
    assert data[0]["title"] == "Ünïcode Tïtle"
    assert data[0]["authors"] == ["Äda Lovelace"]


def test_export_csv_empty_writes_header_only(tmp_path):
    out = tmp_path / "e.csv"
    export_csv([], str(out))
    with out.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        assert list(reader) == []


def test_export_csv_comma_in_author_survives(make_paper, tmp_path):
    p = make_paper(authors=["Smith, John", "Doe, Jane"])
    out = tmp_path / "c.csv"
    export_csv([p], str(out))
    with out.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["authors"] == "Smith, John; Doe, Jane"


def test_export_unknown_format_raises(make_paper, tmp_path):
    with pytest.raises(ValueError):
        export([make_paper()], str(tmp_path / "x.xml"), "xml")


def test_export_json_empty_is_brackets(tmp_path):
    out = tmp_path / "empty.json"
    export_json([], str(out))
    assert out.read_text(encoding="utf-8").strip() == "[]"