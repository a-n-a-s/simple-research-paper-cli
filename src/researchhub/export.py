import csv
import json

from researchhub.models import Paper


CSV_FIELDS = [
    "paper_id",
    "title",
    "authors",
    "abstract",
    "doi",
    "publication_year",
    "source",
    "paper_url",
]


def export_json(papers: list[Paper], path: str) -> None:
    data = [paper.model_dump(mode="json") for paper in papers]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_csv(papers: list[Paper], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for paper in papers:
            row = paper.model_dump(mode="json")
            row["authors"] = "; ".join(paper.authors)
            writer.writerow(row)


def export(papers: list[Paper], path: str, fmt: str) -> None:
    fmt = fmt.strip().lower()
    if fmt == "json":
        export_json(papers, path)
    elif fmt == "csv":
        export_csv(papers, path)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r} (expected 'json' or 'csv')")