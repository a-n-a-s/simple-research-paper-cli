from researchhub.models import Paper


def _normalize_title(title: str) -> str:
    return " ".join(title.strip().lower().split())


def remove_duplicates(
    arxiv_list: list[Paper],
    crossref_list: list[Paper],
) -> list[Paper]:
    seen_titles: set[str] = set()
    results: list[Paper] = []

    for paper in arxiv_list + crossref_list:
        key = _normalize_title(paper.title)
        if not key:
            continue
        if key in seen_titles:
            continue
        seen_titles.add(key)
        results.append(paper)

    return results