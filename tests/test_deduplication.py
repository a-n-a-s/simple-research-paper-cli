from researchhub.deduplication import remove_duplicates


def test_collapses_case_and_whitespace(make_paper):
    a = make_paper(title="Attention Is All You Need", source="arxiv")
    b = make_paper(title="attention   is all you need ", source="crossref")
    assert len(remove_duplicates([a], [b])) == 1


def test_arxiv_wins_ties(make_paper):
    a = make_paper(title="Same", source="arxiv")
    b = make_paper(title="Same", source="crossref")
    out = remove_duplicates([a], [b])
    assert len(out) == 1 and out[0].source == "arxiv"


def test_empty_lists():
    assert remove_duplicates([], []) == []


def test_three_copies_keeps_one(make_paper):
    a = make_paper(title="X")
    b = make_paper(title="x")
    c = make_paper(title=" X ")
    assert len(remove_duplicates([a, b], [c])) == 1