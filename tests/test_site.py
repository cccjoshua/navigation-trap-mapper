from __future__ import annotations

import pytest

from contract import PageInput, SeedInput
from plugin import list_links, map_graph, start_site
from plugin.site import build_site, trap_pages


def explore(seed: int) -> tuple[dict[str, list[str]], int]:
    """What an agent learns by listing every page it has seen, a layer per list_links call, and the calls."""
    start = start_site(SeedInput(seed=seed), None).start_page_id
    seen, frontier, calls = {}, [start], 0
    while frontier:
        calls += 1
        for page in list_links(PageInput(seed=seed, page_ids=frontier[:40]), None).pages:
            seen[page.page_id] = [found.next_page_id for found in page.links]
        listed = set(seen)
        frontier = sorted({there for found in seen.values() for there in found} - listed)
    return seen, calls


def test_a_seed_always_builds_the_same_site() -> None:
    assert build_site(42) == build_site(42)
    assert build_site(42) != build_site(43)


@pytest.mark.parametrize("seed", range(300))
def test_every_site_has_traps_unreachable_pages_and_a_reachable_target(seed: int) -> None:
    site = build_site(seed)
    traps = trap_pages(site)
    assert 3 <= len(traps) <= 9
    assert site.target not in traps and site.start not in traps
    explored, calls = explore(seed)
    assert calls <= 7  # 6 layers at most, plus the start page
    assert site.target in explored
    assert len(explored) < len(site.links)  # some pages are never reachable
    assert set(traps) <= set(explored)


def test_the_tools_agree_with_the_reference_graph() -> None:
    graph = map_graph(SeedInput(seed=7), None)
    site = start_site(SeedInput(seed=7), None)
    assert (site.start_page_id, site.target_page_id) == (graph.start_page_id, graph.target_page_id)
    for page in graph.pages:
        [shown] = list_links(PageInput(seed=7, page_ids=[page.page_id]), None).pages
        assert [found.next_page_id for found in shown.links] == page.links
    ids = [page.page_id for page in graph.pages][:40]
    assert [page.page_id for page in list_links(PageInput(seed=7, page_ids=ids), None).pages] == ids


def test_the_tools_refuse_what_the_site_does_not_have() -> None:
    with pytest.raises(ValueError, match="no page"):
        list_links(PageInput(seed=7, page_ids=["p99"]), None)
    with pytest.raises(ValueError, match="distinct"):
        list_links(PageInput(seed=7, page_ids=["p00", "p00"]), None)
    with pytest.raises(ValueError, match="distinct"):
        list_links(PageInput(seed=7, page_ids=[]), None)
    with pytest.raises(ValueError, match="seed"):
        start_site(SeedInput(seed=-1), None)


@pytest.mark.parametrize("seed", [0, 3, 7, 1_000_000, *range(300)])
def test_one_start_call_and_one_list_call_are_enough_to_find_the_traps(seed: int) -> None:
    site = start_site(SeedInput(seed=seed), None)
    ids = [f"p{number:02d}" for number in range(site.page_count)]
    assert len(ids) <= 40
    links = {page.page_id: [found.next_page_id for found in page.links]
             for page in list_links(PageInput(seed=seed, page_ids=ids), None).pages}
    assert set(links) == set(build_site(seed).links)

    def reach(begin: str, graph: dict[str, list[str]]) -> set[str]:
        seen, todo = {begin}, [begin]
        while todo:
            for there in graph[todo.pop()]:
                if there not in seen:
                    seen.add(there)
                    todo.append(there)
        return seen

    backward: dict[str, list[str]] = {page: [] for page in links}
    for page, found in links.items():
        for there in found:
            backward[there].append(page)
    found_traps = sorted(reach(site.start_page_id, links) - reach(site.target_page_id, backward))
    assert found_traps == map_graph(SeedInput(seed=seed), None).trap_pages
