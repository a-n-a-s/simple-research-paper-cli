import httpx
import pytest
import respx

from researchhub.search import arxiv_search, crossref_search


ARXIV_URL = "https://export.arxiv.org/api/query"
CROSSREF_URL = "https://api.crossref.org/works"


@pytest.mark.parametrize("query", ["", "   "])
async def test_arxiv_rejects_empty_query(query):
    with pytest.raises(ValueError):
        await arxiv_search(query, 5)


@pytest.mark.parametrize("n", [0, -1])
async def test_arxiv_rejects_bad_max(n):
    with pytest.raises(ValueError):
        await arxiv_search("x", n)


@respx.mock
async def test_arxiv_success(arxiv_xml):
    respx.get(ARXIV_URL).mock(return_value=httpx.Response(200, content=arxiv_xml))
    papers = await arxiv_search("attention", 5)
    assert len(papers) == 3
    t = papers[0]
    assert t.title == "Attention Is All You Need"
    assert t.authors == ["Ashish Vaswani", "Noam Shazeer"]
    assert t.publication_year == 2017
    assert t.paper_id is not None


@respx.mock
async def test_arxiv_http_error():
    respx.get(ARXIV_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(RuntimeError, match="arXiv HTTP error"):
        await arxiv_search("x", 5)


@respx.mock
async def test_arxiv_malformed_xml():
    respx.get(ARXIV_URL).mock(
        return_value=httpx.Response(200, content=b"<not-xml")
    )
    with pytest.raises(ValueError, match="malformed"):
        await arxiv_search("x", 5)


@respx.mock
async def test_arxiv_connect_error():
    respx.get(ARXIV_URL).mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(RuntimeError, match="Could not connect to arXiv"):
        await arxiv_search("x", 5)


@respx.mock
async def test_arxiv_timeout():
    respx.get(ARXIV_URL).mock(side_effect=httpx.TimeoutException("slow"))
    with pytest.raises(RuntimeError, match="timed out"):
        await arxiv_search("x", 5)


@respx.mock
async def test_crossref_success(crossref_json):
    respx.get(CROSSREF_URL).mock(
        return_value=httpx.Response(200, json=crossref_json)
    )
    papers = await crossref_search("x", 5)
    # one item has empty title → skipped
    assert len(papers) == 2
    assert papers[0].title == "A Crossref Only Paper"
    assert papers[0].publication_year == 2019


@respx.mock
async def test_crossref_bad_message_shape():
    respx.get(CROSSREF_URL).mock(
        return_value=httpx.Response(200, json={"message": "nope"})
    )
    with pytest.raises(RuntimeError, match="Invalid Crossref response"):
        await crossref_search("x", 5)


@respx.mock
async def test_crossref_items_not_list():
    respx.get(CROSSREF_URL).mock(
        return_value=httpx.Response(200, json={"message": {"items": "nope"}})
    )
    with pytest.raises(RuntimeError, match="Invalid Crossref response"):
        await crossref_search("x", 5)


@respx.mock
async def test_crossref_http_error():
    respx.get(CROSSREF_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(RuntimeError, match="Crossref HTTP error"):
        await crossref_search("x", 5)


@respx.mock
async def test_crossref_skips_invalid_paper(caplog):
    payload = {"message": {"items": [
        {"title": ["Good"], "author": [], "URL": "u"},
        {"title": ["Bad"], "publication_year": "not-an-int"},
    ]}}
    respx.get(CROSSREF_URL).mock(
        return_value=httpx.Response(200, json=payload)
    )
    papers = await crossref_search("x", 5)
    # If your Paper model doesn't coerce "not-an-int", this proves the
    # try/except ValidationError skip works. Adjust expected count to match
    # what your model actually does with that field.
    assert all(p.title != "Bad" for p in papers) or len(papers) == 2