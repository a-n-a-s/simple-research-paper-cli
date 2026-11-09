
import logging
import httpx
import feedparser

from pydantic import ValidationError
from researchhub.models import Paper


logger = logging.getLogger(__name__)


async def arxiv_search(query: str, max_results: int) -> list[Paper]:

    if not query.strip():
        raise ValueError("Search query cannot be empty")

    if max_results <= 0:
        raise ValueError("max_results must be greater than zero")

    arxiv_papers = []
    arxiv_url = "https://export.arxiv.org/api/query"

    arxiv_params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:

            response = await client.get(
                arxiv_url,
                params=arxiv_params,
                timeout=10
            )

            response.raise_for_status()

            arxiv_feed = feedparser.parse(response.content)

            if arxiv_feed.bozo:
                raise ValueError("Invalid or malformed arXiv XML response")

            for paper in arxiv_feed.entries:

                title = paper.get("title")
                if not title:
                    continue

                authors = [
                    a.get("name")
                    for a in paper.get("authors", [])
                    if a.get("name")
                ]

                abstract = paper.get("summary")
                source = paper.get("link")

                published_parsed = paper.get("published_parsed")
                publication_year = (
                    published_parsed.tm_year
                    if published_parsed else None
                )

                try:
                    arxiv_paper = Paper(
                        title=title,
                        authors=authors,
                        publication_year=publication_year,
                        abstract=abstract,
                        source=source
                    )

                    arxiv_papers.append(arxiv_paper)

                except ValidationError as e:
                    logger.warning(
                        "Skipping invalid arXiv paper: %s", e
                    )

    except httpx.Timeout as e:
        raise RuntimeError("arXiv API request timed out") from e

    except httpx.ConnectError as e:
        raise RuntimeError("Could not connect to arXiv") from e

    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"arXiv HTTP error: {e}") from e

    except httpx.RequestException as e:
        raise RuntimeError(f"arXiv request failed: {e}") from e

    return arxiv_papers


async def crossref_search(query: str, max_results: int) -> list[Paper]:

    if not query.strip():
        raise ValueError("Search query cannot be empty")

    if max_results <= 0:
        raise ValueError("max_results must be greater than zero")

    crossref_url = "https://api.crossref.org/works"

    crossref_params = {
        "query": query,
        "rows": max_results
    }

    crossref_papers = []

    try:
        with httpx.AsyncClient() as client:

            response = await client.get(
                crossref_url,
                params=crossref_params,
                timeout=10
            )

            response.raise_for_status()

            crossref_data = response.json()

            message = crossref_data.get("message")

            if not isinstance(message, dict):
                raise ValueError("Invalid Crossref response structure")

            papers = message.get("items")

            if not isinstance(papers, list):
                raise ValueError("Crossref items must be a list")

            for paper in papers:

                title_list = paper.get("title", [])

                if not title_list or not title_list[0]:
                    continue

                authors = [
                    f"{author.get('given', '')} "
                    f"{author.get('family', '')}".strip()
                    for author in paper.get("author", [])
                    if author.get("given") or author.get("family")
                ]

                date_parts = (
                    paper.get("published", {})
                    .get("date-parts", [])
                )

                publication_year = (
                    date_parts[0][0]
                    if date_parts and date_parts[0]
                    else None
                )

                try:
                    crossref_paper = Paper(
                        title=title_list[0],
                        authors=authors,
                        publication_year=publication_year,
                        abstract=paper.get("abstract"),
                        source=paper.get("URL")
                    )

                    crossref_papers.append(crossref_paper)

                except ValidationError as e:
                    logger.warning(
                        "Skipping invalid Crossref paper: %s", e
                    )

    except httpx.ConnectError as e:
        raise RuntimeError(
            "Could not connect to Crossref"
        ) from e

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Crossref HTTP error: {e}"
        ) from e

    except httpx.RequestError as e:
        raise RuntimeError(
            f"Crossref request failed: {e}"
        ) from e

    except ValueError as e:
        raise RuntimeError(
            f"Invalid Crossref response: {e}"
        ) from e

    return crossref_papers
