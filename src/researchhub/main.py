import asyncio

from .deduplication import remove_duplicates
from .export import export
from .search import arxiv_search, crossref_search


async def run(query: str, max_results: int) -> None:
    results = await asyncio.gather(
        arxiv_search(query, max_results),
        crossref_search(query, max_results),
        return_exceptions=True,
    )

    arxiv_res, crossref_res = results

    if isinstance(arxiv_res, Exception):
        print(f"arXiv search failed: {arxiv_res}")
        arxiv_papers = []
    else:
        arxiv_papers = arxiv_res

    if isinstance(crossref_res, Exception):
        print(f"Crossref search failed: {crossref_res}")
        crossref_papers = []
    else:
        crossref_papers = crossref_res

    papers = remove_duplicates(arxiv_papers, crossref_papers)

    if not papers:
        print("No papers found.")
        return

    print(f"\nFound {len(papers)} unique paper(s):\n")
    for i, paper in enumerate(papers, start=1):
        print(f"{i}. {paper.title}")
        if paper.authors:
            print(f"   Authors: {', '.join(paper.authors)}")
        if paper.publication_year:
            print(f"   Year: {paper.publication_year}")
        if paper.source:
            print(f"   Source: {paper.source}")
        print()

    fmt = input("Export as (json/csv): ").strip().lower()
    if fmt not in {"json", "csv"}:
        print("Format must be 'json' or 'csv'. Skipping export.")
        return

    path = input(f"Output file path (default results.{fmt}): ").strip()
    if not path:
        path = f"results.{fmt}"

    export(papers, path, fmt)
    print(f"Exported {len(papers)} paper(s) to {path}")


def get_inputs() -> tuple[str, int]:
    query = input("Enter the topic you want to search papers: ").strip()
    if not query:
        raise SystemExit("Search query cannot be empty.")

    raw = input("Maximum number of results you want (default 50): ").strip()
    if not raw:
        return query, 50

    try:
        max_results = int(raw)
    except ValueError:
        raise SystemExit("max_results must be a positive integer.")

    if max_results <= 0:
        raise SystemExit("max_results must be greater than zero.")

    return query, max_results


def main() -> None:
    query, max_results = get_inputs()
    asyncio.run(run(query, max_results))


if __name__ == "__main__":
    main()