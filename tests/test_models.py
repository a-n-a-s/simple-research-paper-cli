
import pytest
from pydantic import ValidationError
from researchhub.models import Paper


# Test 1: Valid Paper object
def test_valid_paper():
    paper = Paper(
        paper_id=1,
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        abstract="A paper introducing the Transformer architecture.",
        publication_year=2017,
        doi="10.48550/arXiv.1706.03762",
        source="arXiv",
        paper_url="https://arxiv.org/abs/1706.03762"
    )

    assert paper.paper_id == 1
    assert paper.title == "Attention Is All You Need"
    assert len(paper.authors) == 2
    assert paper.publication_year == 2017


# Test 2: Optional fields can be None
def test_optional_fields():
    paper = Paper(
        paper_id=2,
        title="Machine Learning Research",
        authors=["John Doe"],
        abstract="An introduction to ML.",
        publication_year=2024
    )

    assert paper.doi is None
    assert paper.source is None
    assert paper.paper_url is None


# Test 3: Invalid paper_id
def test_invalid_paper_id():
    with pytest.raises(ValidationError):
        Paper(
            paper_id="invalid",
            title="Test Paper",
            authors=["John Doe"],
            abstract="Test abstract",
            publication_year=2024
        )


# Test 4: Invalid authors type
def test_invalid_authors():
    with pytest.raises(ValidationError):
        Paper(
            paper_id=3,
            title="Test Paper",
            authors="John Doe",
            abstract="Test abstract",
            publication_year=2024
        )


# Test 5: Missing required field
def test_missing_required_field():
    with pytest.raises(ValidationError):
        Paper(
            paper_id=4,
            authors=["John Doe"],
            abstract="Test abstract",
            publication_year=2024
        )
